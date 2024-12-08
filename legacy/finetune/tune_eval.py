# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

import os
import shutil
from pathlib import Path

import dataclasses
import fire
import random
import torch
import torch.optim as optim
from peft import get_peft_model, prepare_model_for_kbit_training, PeftModel
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP,
    ShardingStrategy
)

from torch.distributed.fsdp.fully_sharded_data_parallel import CPUOffload
from torch.optim.lr_scheduler import StepLR
from transformers import (
    AutoTokenizer,
    LlamaForCausalLM,
    LlamaConfig,
)
from transformers.models.llama.modeling_llama import LlamaDecoderLayer

from llama_recipes.configs import fsdp_config as FSDP_CONFIG
from llama_recipes.configs import train_config as TRAIN_CONFIG
from llama_recipes.data.concatenator import ConcatDataset
from llama_recipes.policies import AnyPrecisionAdamW, apply_fsdp_checkpointing

# from llama_recipes.utils import fsdp_auto_wrap_policy
from utils.fsdp_utils import fsdp_auto_wrap_policy, hsdp_device_mesh

# from llama_recipes.utils.config_utils import (
#     update_config,
#     generate_peft_config,
#     generate_dataset_config,
#     get_dataloader_kwargs,
# )
from utils.config_utils import (
    update_config,
    generate_peft_config,
    generate_dataset_config,
    get_dataloader_kwargs,
)

# from llama_recipes.utils.dataset_utils import get_preprocessed_dataset
from utils.dataset_utils import get_preprocessed_dataset

# from llama_recipes.utils.train_utils import (
#     train,
#     freeze_transformer_layers,
#     setup,
#     setup_environ_flags,
#     clear_gpu_cache,
#     print_model_size,
#     get_policies,
# )
from utils.train_utils import (
    train,
    freeze_transformer_layers,
    setup,
    setup_environ_flags,
    clear_gpu_cache,
    print_model_size,
    get_policies,
)

from accelerate.utils import is_xpu_available

from llama_recipes.model_checkpointing import save_model_checkpoint

import warnings
warnings.filterwarnings("ignore")


# Import evaluation function from eval.py
import lm_eval
from lm_eval import tasks
from eval import *

def setup_wandb(train_config, fsdp_config, **kwargs):
    try:
        import wandb
    except ImportError:
        raise ImportError(
            "You are trying to use wandb which is not currently installed. "
            "Please install it using pip install wandb"
        )
    from llama_recipes.configs import wandb_config as WANDB_CONFIG
    wandb_config = WANDB_CONFIG()
    update_config(wandb_config, **kwargs)
    init_dict = dataclasses.asdict(wandb_config)
    run = wandb.init(**init_dict)
    run.config.update(train_config)
    run.config.update(fsdp_config, allow_val_change=True)
    return run


def main(**kwargs):
    # Update the configuration for the training and sharding process
    train_config, fsdp_config = TRAIN_CONFIG(), FSDP_CONFIG()
    update_config((train_config, fsdp_config), **kwargs)
    # Set the seeds for reproducibility
    if is_xpu_available():
        torch.xpu.manual_seed(train_config.seed)
    torch.manual_seed(train_config.seed)
    random.seed(train_config.seed)

    if train_config.enable_fsdp:
        setup()
        # torchrun specific
        local_rank = int(os.environ["LOCAL_RANK"])
        rank = int(os.environ["RANK"])
        world_size = int(os.environ["WORLD_SIZE"])

    if torch.distributed.is_initialized():
        if is_xpu_available():
            torch.xpu.set_device(local_rank)
        elif torch.cuda.is_available():
            torch.cuda.set_device(local_rank)
        clear_gpu_cache(local_rank)
        setup_environ_flags(rank)

    wandb_run = None

    if train_config.use_wandb:
        if not train_config.enable_fsdp or rank==0:
            wandb_run = setup_wandb(train_config, fsdp_config, **kwargs)

    # Load the pre-trained model and setup its configuration
    use_cache = False if train_config.enable_fsdp else None
    if train_config.enable_fsdp and train_config.low_cpu_fsdp:
        """
        for FSDP, we can save cpu memory by loading pretrained model on rank0 only.
        this avoids cpu oom when loading large models like llama 70B, in which case
        model alone would consume 2+TB cpu mem (70 * 4 * 8). This will add some comms
        overhead and currently requires latest nightly.
        """
        if rank == 0:
            model = LlamaForCausalLM.from_pretrained(
                train_config.model_name,
                # load_in_8bit=True if train_config.quantization else None,
                load_in_4bit=True if train_config.quantization else None,
                device_map="auto" if train_config.quantization else None,
                use_cache=use_cache,
                attn_implementation="sdpa" if train_config.use_fast_kernels else None,
            )
        else:
            llama_config = LlamaConfig.from_pretrained(train_config.model_name)
            llama_config.use_cache = use_cache
            with torch.device("meta"):
                model = LlamaForCausalLM(llama_config)

    else:
        model = LlamaForCausalLM.from_pretrained(
            train_config.model_name,
            # load_in_8bit=True if train_config.quantization else None,
            load_in_4bit=True if train_config.quantization else None,
            device_map="auto" if train_config.quantization else None,
            use_cache=use_cache,
            attn_implementation="sdpa" if train_config.use_fast_kernels else None,
        )

    # Load the tokenizer and add special tokens
    tokenizer = AutoTokenizer.from_pretrained(train_config.model_name if train_config.tokenizer_name is None else train_config.tokenizer_name)
    tokenizer.pad_token_id = tokenizer.eos_token_id

    # If there is a mismatch between tokenizer vocab size and embedding matrix,
    # throw a warning and then expand the embedding matrix
    if len(tokenizer) > model.get_input_embeddings().weight.shape[0]:
        print("WARNING: Resizing the embedding matrix to match the tokenizer vocab size.")
        model.resize_token_embeddings(len(tokenizer))

    print_model_size(model, train_config, rank if train_config.enable_fsdp else 0)

    # Prepare the model for int8 training if quantization is enabled
    if train_config.quantization:
        model = prepare_model_for_kbit_training(model)

    # Convert the model to bfloat16 if fsdp and pure_bf16 is enabled
    if train_config.enable_fsdp and fsdp_config.pure_bf16:
        model.to(torch.bfloat16)

    if train_config.use_peft:
        # Load the pre-trained peft model checkpoint and setup its configuration
        if train_config.from_peft_checkpoint:
            model = PeftModel.from_pretrained(model, train_config.from_peft_checkpoint, is_trainable=True)
            peft_config = model.peft_config()
        # Generate the peft config and start fine-tuning from original model
        else:
            peft_config = generate_peft_config(train_config, kwargs)
            model = get_peft_model(model, peft_config)
        if wandb_run:
            wandb_run.config.update(peft_config)
        model.print_trainable_parameters()


    hsdp_device_mesh = None
    if fsdp_config.hsdp and fsdp_config.sharding_strategy == ShardingStrategy.HYBRID_SHARD:
        hsdp_device_mesh = hsdp_device_mesh(replica_group_size=fsdp_config.replica_group_size, sharding_group_size=fsdp_config.sharding_group_size)
        print("HSDP device mesh is ready")

    #setting up FSDP if enable_fsdp is enabled
    if train_config.enable_fsdp:
        if not train_config.use_peft and train_config.freeze_layers:
            freeze_transformer_layers(model, train_config.num_freeze_layers)

        mixed_precision_policy, wrapping_policy = get_policies(fsdp_config, rank)
        my_auto_wrapping_policy = fsdp_auto_wrap_policy(model, LlamaDecoderLayer)

        device_id = 0
        if is_xpu_available():
            device_id = torch.xpu.current_device()
        elif torch.cuda.is_available():
            device_id = torch.cuda.current_device()

        model = FSDP(
            model,
            auto_wrap_policy= my_auto_wrapping_policy if train_config.use_peft else wrapping_policy,
            cpu_offload=CPUOffload(offload_params=True) if fsdp_config.fsdp_cpu_offload else None,
            mixed_precision=mixed_precision_policy if not fsdp_config.pure_bf16 else None,
            sharding_strategy=fsdp_config.sharding_strategy,
            device_mesh=hsdp_device_mesh,
            device_id=device_id,
            limit_all_gathers=True,
            sync_module_states=train_config.low_cpu_fsdp,
            param_init_fn=(lambda module: module.to_empty(device=torch.device("cuda"), recurse=False))
            if train_config.low_cpu_fsdp and rank != 0 else None,
        )
        if fsdp_config.fsdp_activation_checkpointing:
            apply_fsdp_checkpointing(model)
    elif not train_config.quantization and not train_config.enable_fsdp:
        if is_xpu_available():
            model.to("xpu:0")
        elif torch.cuda.is_available():
            model.to("cuda")

    dataset_config = generate_dataset_config(train_config, kwargs)

     # Load and preprocess the dataset for training and validation
    dataset_train = get_preprocessed_dataset(
        tokenizer,
        dataset_config,
        split="train",
    )

    if not train_config.enable_fsdp or rank == 0:
        print(f"--> Training Set Length = {len(dataset_train)}")

    dataset_val = get_preprocessed_dataset(
        tokenizer,
        dataset_config,
        split="test",
    )
    if not train_config.enable_fsdp or rank == 0:
        print(f"--> Validation Set Length = {len(dataset_val)}")

    if train_config.batching_strategy == "packing":
        dataset_train = ConcatDataset(dataset_train, chunk_size=train_config.context_length)

    train_dl_kwargs = get_dataloader_kwargs(train_config, dataset_train, tokenizer, "train")

    # Create DataLoaders for the training and validation dataset
    train_dataloader = torch.utils.data.DataLoader(
        dataset_train,
        num_workers=train_config.num_workers_dataloader,
        pin_memory=True,
        **train_dl_kwargs,
    )

    eval_dataloader = None
    if train_config.run_validation:
        if train_config.batching_strategy == "packing":
            dataset_val = ConcatDataset(dataset_val, chunk_size=train_config.context_length)

        val_dl_kwargs = get_dataloader_kwargs(train_config, dataset_val, tokenizer, "val")

        eval_dataloader = torch.utils.data.DataLoader(
            dataset_val,
            num_workers=train_config.num_workers_dataloader,
            pin_memory=True,
            **val_dl_kwargs,
        )
        if len(eval_dataloader) == 0:
            raise ValueError("The eval set size is too small for dataloader to load even one batch. Please increase the size of eval set.")
        else:
            print(f"--> Num of Validation Set Batches loaded = {len(eval_dataloader)}")

    # Initialize the optimizer and learning rate scheduler
    if fsdp_config.pure_bf16 and fsdp_config.optimizer == "anyprecision":
        optimizer = AnyPrecisionAdamW(
            model.parameters(),
            lr=train_config.lr,
            momentum_dtype=torch.bfloat16,
            variance_dtype=torch.bfloat16,
            use_kahan_summation=False,
            weight_decay=train_config.weight_decay,
        )
    else:
        optimizer = optim.AdamW(
            model.parameters(),
            lr=train_config.lr,
            weight_decay=train_config.weight_decay,
        )
    scheduler = StepLR(optimizer, step_size=1, gamma=train_config.gamma)

    # # Start the training process
    # results = train(
    #     model,
    #     train_dataloader,
    #     eval_dataloader,
    #     tokenizer,
    #     optimizer,
    #     scheduler,
    #     train_config.gradient_accumulation_steps,
    #     train_config,
    #     fsdp_config if train_config.enable_fsdp else None,
    #     local_rank if train_config.enable_fsdp else None,
    #     rank if train_config.enable_fsdp else None,
    #     wandb_run,
    # )
    # if not train_config.enable_fsdp or rank==0:
    #     [print(f'Key: {k}, Value: {v}') for k, v in results.items()]
    #     if train_config.use_wandb:
    #         for k,v in results.items():
    #             wandb_run.summary[k] = v


    # Initialize variables to track best performance
    best_accuracy = 0
    best_epoch = -1
    all_results = []

    # Ensure the output directory exists
    os.makedirs(train_config.output_dir, exist_ok=True)

    def eval_callback(epoch, model, train_config, optimizer, rank):
        nonlocal best_accuracy, best_epoch, all_results

        # Save the current model
        current_model_path = os.path.join(train_config.output_dir, f"model_epoch_{epoch}")
        if not train_config.enable_fsdp or rank == 0:
            if train_config.use_peft:
                model.save_pretrained(current_model_path)
            else:
                save_model_checkpoint(model, optimizer, rank, train_config, epoch=epoch, output_dir=current_model_path)

        # Ensure all processes have finished saving
        if train_config.enable_fsdp:
            torch.distributed.barrier()

        # Evaluate the model
        eval_results = evaluate_model(model, train_config, epoch)
        
       # Extract results for clinical_knowledge and college_medicine
        clinical_knowledge_acc = eval_results["results"]["mmlu_clinical_knowledge"]["acc,none"]
        college_medicine_acc = eval_results["results"]["mmlu_college_medicine"]["acc,none"]

        # Store results for this epoch
        all_results.append({
            "epoch": epoch + 1,
            "clinical_knowledge_acc": clinical_knowledge_acc,
            "college_medicine_acc": college_medicine_acc
        })

        # Check if current accuracy is better than the best so far
        if clinical_knowledge_acc > best_accuracy:
            best_accuracy = clinical_knowledge_acc
            best_epoch = epoch
            
            # Rename the current model to "best_model"
            best_model_path = os.path.join(train_config.output_dir, "best_model")
            if not train_config.enable_fsdp or rank == 0:
                if os.path.exists(best_model_path):
                    shutil.rmtree(best_model_path)
                os.rename(current_model_path, best_model_path)
        else:
            # Remove the current model if it's not the best
            if not train_config.enable_fsdp or rank == 0:
                shutil.rmtree(current_model_path)

        # Log the results
        if not train_config.enable_fsdp or rank == 0:
            print(f"Epoch {epoch + 1} evaluation results:")
            print(f"Clinical Knowledge Accuracy: {clinical_knowledge_acc}")
            
            if train_config.use_wandb:
                wandb_run.log({
                    "eval/clinical_knowledge_acc": clinical_knowledge_acc,
                    "epoch": epoch + 1,
                })

    def evaluate_model(model, train_config, epoch):
        pretrain_str = f'pretrained={train_config.model_name}'
        # dtype_str = 'dtype="float"'
        peft_str = f'peft={os.path.join(train_config.output_dir, f"model_epoch_{epoch}")}'
        # model_arg_str = str(pretrain_str+','+dtype_str+','+peft_str)
        model_arg_str = str(pretrain_str+','+peft_str)
        print(f"model_arg_str: {model_arg_str}")

        results = lm_eval.simple_evaluate(
            model='hf',
            model_args=model_arg_str,
            tasks=["mmlu"],
            batch_size=8,
            limit=2000,
        )
        return results

    # Start the training process
    results = train(
        model,
        train_dataloader,
        eval_dataloader,
        tokenizer,
        optimizer,
        scheduler,
        train_config.gradient_accumulation_steps,
        train_config,
        fsdp_config if train_config.enable_fsdp else None,
        local_rank if train_config.enable_fsdp else None,
        rank if train_config.enable_fsdp else None,
        wandb_run,
        eval_callback=eval_callback
    )

    # Save the results for all epochs and the best performance to a file
    if not train_config.enable_fsdp or rank == 0:
        best_model_path = os.path.join(train_config.output_dir, "best_model")
        performance_file = os.path.join(best_model_path, "performance_results.txt")
        
        with open(performance_file, "w") as f:
            f.write("Results for all epochs:\n")
            f.write("------------------------\n")
            for result in all_results:
                f.write(f"Epoch: {result['epoch']}\n")
                f.write(f"Clinical Knowledge Accuracy: {result['clinical_knowledge_acc']:.4f}\n")
                f.write(f"College Medicine Accuracy: {result['college_medicine_acc']:.4f}\n")
                f.write("------------------------\n")
            
            f.write("\nBest Performance:\n")
            f.write("------------------------\n")
            f.write(f"Epoch: {best_epoch + 1}\n")
            f.write(f"Clinical Knowledge Accuracy: {best_accuracy:.4f}\n")
            f.write(f"College Medicine Accuracy: {all_results[best_epoch]['college_medicine_acc']:.4f}\n")
        
        print(f"Performance results saved to {performance_file}")

    if train_config.use_wandb:
        wandb_run.summary["best_epoch"] = best_epoch + 1
        wandb_run.summary["best_clinical_knowledge_acc"] = best_accuracy

    return results


if __name__ == "__main__":
    fire.Fire(main)