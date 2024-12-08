"""
spaCy Clinical Text Tokenizer

Built via manual inspection of clinical notes from:
- MIMIC-III
- Stanford Health Care
- THYME
- i2b2/n2c2 2009 Medications

"""
import re
import functools
from spacy.symbols import ORTH
from spacy.tokenizer import Tokenizer


special_cases = [
    ("A.A.A.", [{ORTH: "A.A.A."}]),
    ("A.A.A.S.", [{ORTH: "A.A.A.S."}]),
    ("A.A.B.B.", [{ORTH: "A.A.B.B."}]),
    ("A.A.C.P.", [{ORTH: "A.A.C.P."}]),
    ("A.A.D.", [{ORTH: "A.A.D."}]),
    ("A.A.D.P.", [{ORTH: "A.A.D.P."}]),
    ("A.A.D.R.", [{ORTH: "A.A.D.R."}]),
    ("A.A.D.S.", [{ORTH: "A.A.D.S."}]),
    ("A.A.E.", [{ORTH: "A.A.E."}]),
    ("A.A.F.P.", [{ORTH: "A.A.F.P."}]),
    ("A.A.G.P.", [{ORTH: "A.A.G.P."}]),
    ("A.A.I.", [{ORTH: "A.A.I."}]),
    ("A.A.I.D.", [{ORTH: "A.A.I.D."}]),
    ("A.A.I.N.", [{ORTH: "A.A.I.N."}]),
    ("A.A.M.A.", [{ORTH: "A.A.M.A."}]),
    ("A.A.M.C.", [{ORTH: "A.A.M.C."}]),
    ("A.A.M.D.", [{ORTH: "A.A.M.D."}]),
    ("A.A.M.R.L.", [{ORTH: "A.A.M.R.L."}]),
    ("A.A.O.", [{ORTH: "A.A.O."}]),
    ("A.A.O.P.", [{ORTH: "A.A.O.P."}]),
    ("A.A.P.", [{ORTH: "A.A.P."}]),
    ("A.A.P.A.", [{ORTH: "A.A.P.A."}]),
    ("A.A.P.B.", [{ORTH: "A.A.P.B."}]),
    ("A.A.P.M.R.", [{ORTH: "A.A.P.M.R."}]),
    ("A.A.P.S.", [{ORTH: "A.A.P.S."}]),
    ("A.B.E.P.P.", [{ORTH: "A.B.E.P.P."}]),
    ("A.C.", [{ORTH: "A.C."}]),
    ("A.C.A.", [{ORTH: "A.C.A."}]),
    ("A.C.G.", [{ORTH: "A.C.G."}]),
    ("A.C.H.A.", [{ORTH: "A.C.H.A."}]),
    ("A.C.N.M.", [{ORTH: "A.C.N.M."}]),
    ("A.C.O.G.", [{ORTH: "A.C.O.G."}]),
    ("A.C.O.H.A.", [{ORTH: "A.C.O.H.A."}]),
    ("A.C.O.O.G.", [{ORTH: "A.C.O.O.G."}]),
    ("A.C.O.S.", [{ORTH: "A.C.O.S."}]),
    ("A.C.P.", [{ORTH: "A.C.P."}]),
    ("A.C.R.", [{ORTH: "A.C.R."}]),
    ("A.C.S.", [{ORTH: "A.C.S."}]),
    ("A.C.S.M.", [{ORTH: "A.C.S.M."}]),
    ("A.D.", [{ORTH: "A.D."}]),
    ("A.D.A.", [{ORTH: "A.D.A."}]),
    ("A.E.", [{ORTH: "A.E."}]),
    ("A.E.S.", [{ORTH: "A.E.S."}]),
    ("A.G.A.", [{ORTH: "A.G.A."}]),
    ("A.G.S.", [{ORTH: "A.G.S."}]),
    ("A.H.A.", [{ORTH: "A.H.A."}]),
    ("A.H.P.", [{ORTH: "A.H.P."}]),
    ("A.H.S.", [{ORTH: "A.H.S."}]),
    ("A.I.", [{ORTH: "A.I."}]),
    ("A.I.C.", [{ORTH: "A.I.C."}]),
    ("A.I.H.", [{ORTH: "A.I.H."}]),
    ("A.I.H.A.", [{ORTH: "A.I.H.A."}]),
    ("A.L.A.", [{ORTH: "A.L.A."}]),
    ("A.L.R.O.S.", [{ORTH: "A.L.R.O.S."}]),
    ("A.M.", [{ORTH: "A.M."}]),
    ("A.M.A.", [{ORTH: "A.M.A."}]),
    ("A.M.R.L.", [{ORTH: "A.M.R.L."}]),
    ("A.M.S.", [{ORTH: "A.M.S."}]),
    ("A.M.S.A.", [{ORTH: "A.M.S.A."}]),
    ("A.M.W.A.", [{ORTH: "A.M.W.A."}]),
    ("A.N.A.", [{ORTH: "A.N.A."}]),
    ("A.O.A.", [{ORTH: "A.O.A."}]),
    ("A.O.P.A.", [{ORTH: "A.O.P.A."}]),
    ("A.O.S.", [{ORTH: "A.O.S."}]),
    ("A.O.T.A.", [{ORTH: "A.O.T.A."}]),
    ("A.P.A.", [{ORTH: "A.P.A."}]),
    ("A.P.H.A.", [{ORTH: "A.P.H.A."}]),
    ("A.P.M.", [{ORTH: "A.P.M."}]),
    ("A.P.S.", [{ORTH: "A.P.S."}]),
    ("A.P.T.A.", [{ORTH: "A.P.T.A."}]),
    ("A.Ph.A.", [{ORTH: "A.Ph.A."}]),
    ("A.R.C.", [{ORTH: "A.R.C."}]),
    ("A.R.M.H.", [{ORTH: "A.R.M.H."}]),
    ("A.R.N.M.D.", [{ORTH: "A.R.N.M.D."}]),
    ("A.R.O.", [{ORTH: "A.R.O."}]),
    ("A.R.R.S.", [{ORTH: "A.R.R.S."}]),
    ("A.R.S.", [{ORTH: "A.R.S."}]),
    ("A.R.T.", [{ORTH: "A.R.T."}]),
    ("A.S.A.I.O.", [{ORTH: "A.S.A.I.O."}]),
    ("A.S.B.", [{ORTH: "A.S.B."}]),
    ("A.S.C.H.", [{ORTH: "A.S.C.H."}]),
    ("A.S.C.I.", [{ORTH: "A.S.C.I."}]),
    ("A.S.C.L.T.", [{ORTH: "A.S.C.L.T."}]),
    ("A.S.C.P.", [{ORTH: "A.S.C.P."}]),
    ("A.S.G.", [{ORTH: "A.S.G."}]),
    ("A.S.H.", [{ORTH: "A.S.H."}]),
    ("A.S.H.A.", [{ORTH: "A.S.H.A."}]),
    ("A.S.H.I.", [{ORTH: "A.S.H.I."}]),
    ("A.S.H.P.", [{ORTH: "A.S.H.P."}]),
    ("A.S.I.I.", [{ORTH: "A.S.I.I."}]),
    ("A.S.I.M.", [{ORTH: "A.S.I.M."}]),
    ("A.S.M.", [{ORTH: "A.S.M."}]),
    ("A.S.P.", [{ORTH: "A.S.P."}]),
    ("A.S.R.T.", [{ORTH: "A.S.R.T."}]),
    ("A.S.T.M.H.", [{ORTH: "A.S.T.M.H."}]),
    ("A.U.", [{ORTH: "A.U."}]),
    ("Act.", [{ORTH: "Act."}]),
    ("Alta.", [{ORTH: "Alta."}]),
    ("Anat.", [{ORTH: "Anat."}]),
    ("Apr.", [{ORTH: "Apr."}]),
    ("Aq.", [{ORTH: "Aq."}]),
    ("As.M.", [{ORTH: "As.M."}]),
    ("Au.D.", [{ORTH: "Au.D."}]),
    ("Aug.", [{ORTH: "Aug."}]),
    ("B.A.", [{ORTH: "B.A."}]),
    ("B.B.B.", [{ORTH: "B.B.B."}]),
    ("B.D.A.", [{ORTH: "B.D.A."}]),
    ("B.D.S.", [{ORTH: "B.D.S."}]),
    ("B.D.Sc.", [{ORTH: "B.D.Sc."}]),
    ("B.F.A.", [{ORTH: "B.F.A."}]),
    ("B.L.R.O.A.", [{ORTH: "B.L.R.O.A."}]),
    ("B.M.", [{ORTH: "B.M."}]),
    ("B.M.A.", [{ORTH: "B.M.A."}]),
    ("B.M.S.", [{ORTH: "B.M.S."}]),
    ("B.O.A.", [{ORTH: "B.O.A."}]),
    ("B.P.", [{ORTH: "B.P."}]),
    ("B.P.A.", [{ORTH: "B.P.A."}]),
    ("B.P.H.", [{ORTH: "B.P.H."}]),
    ("B.R.S.", [{ORTH: "B.R.S."}]),
    ("B.S.", [{ORTH: "B.S."}]),
    ("B.S.N.", [{ORTH: "B.S.N."}]),
    ("B.T.U.", [{ORTH: "B.T.U."}]),
    ("Bact.", [{ORTH: "Bact."}]),
    ("Blvd.", [{ORTH: "Blvd."}]),
    ("Bull.", [{ORTH: "Bull."}]),
    ("C.", [{ORTH: "C."}]),
    ("C.A.P.", [{ORTH: "C.A.P."}]),
    ("C.D.", [{ORTH: "C.D."}]),
    ("C.H.A.", [{ORTH: "C.H.A."}]),
    ("C.I.H.", [{ORTH: "C.I.H."}]),
    ("C.I.N.P.", [{ORTH: "C.I.N.P."}]),
    ("C.I.O.M.S.", [{ORTH: "C.I.O.M.S."}]),
    ("C.M.A.", [{ORTH: "C.M.A."}]),
    ("C.N.A.", [{ORTH: "C.N.A."}]),
    ("C.N.M.", [{ORTH: "C.N.M."}]),
    ("C.O.A.", [{ORTH: "C.O.A."}]),
    ("C.O.S.", [{ORTH: "C.O.S."}]),
    ("C.P.H.", [{ORTH: "C.P.H."}]),
    ("C.R.N.A.", [{ORTH: "C.R.N.A."}]),
    ("C.R.N.P.", [{ORTH: "C.R.N.P."}]),
    ("C.S.A.A.", [{ORTH: "C.S.A.A."}]),
    ("C.S.G.B.I.", [{ORTH: "C.S.G.B.I."}]),
    ("C.T.A.", [{ORTH: "C.T.A."}]),
    ("Cel.", [{ORTH: "Cel."}]),
    ("Ch.", [{ORTH: "Ch."}]),
    ("Colo.", [{ORTH: "Colo."}]),
    ("Conn.", [{ORTH: "Conn."}]),
    ("Cx.", [{ORTH: "Cx."}]),
    ("D.", [{ORTH: "D."}]),
    ("D.A.", [{ORTH: "D.A."}]),
    ("D.A.H.", [{ORTH: "D.A.H."}]),
    ("D.C.", [{ORTH: "D.C."}]),
    ("D.C.F.", [{ORTH: "D.C.F."}]),
    ("D.C.H.", [{ORTH: "D.C.H."}]),
    ("D.C.O.G.", [{ORTH: "D.C.O.G."}]),
    ("D.D.S.", [{ORTH: "D.D.S."}]),
    ("D.D.Sc.", [{ORTH: "D.D.Sc."}]),
    ("D.Hg.", [{ORTH: "D.Hg."}]),
    ("D.Hy.", [{ORTH: "D.Hy."}]),
    ("D.J.", [{ORTH: "D.J."}]),
    ("D.M.R.D.", [{ORTH: "D.M.R.D."}]),
    ("D.M.R.T.", [{ORTH: "D.M.R.T."}]),
    ("D.O.", [{ORTH: "D.O."}]),
    ("D.O.A.", [{ORTH: "D.O.A."}]),
    ("D.P.", [{ORTH: "D.P."}]),
    ("D.P.H.", [{ORTH: "D.P.H."}]),
    ("D.P.M.", [{ORTH: "D.P.M."}]),
    ("D.S.C.", [{ORTH: "D.S.C."}]),
    ("D.T.P.", [{ORTH: "D.T.P."}]),
    ("D.W.", [{ORTH: "D.W."}]),
    ("Dec.", [{ORTH: "Dec."}]),
    ("Deg.", [{ORTH: "Deg."}]),
    ("Det.", [{ORTH: "Det."}]),
    ("Dn.", [{ORTH: "Dn."}]),
    ("Dr.", [{ORTH: "Dr."}]),
    ("Dr.P.H.", [{ORTH: "Dr.P.H."}]),
    ("E.F.", [{ORTH: "E.F."}]),
    ("E.M.S.", [{ORTH: "E.M.S."}]),
    ("E.R.A.", [{ORTH: "E.R.A."}]),
    ("Eur.", [{ORTH: "Eur."}]),
    ("Extr.", [{ORTH: "Extr."}]),
    ("F.", [{ORTH: "F."}]),
    ("F.A.C.D.", [{ORTH: "F.A.C.D."}]),
    ("F.A.C.O.G.", [{ORTH: "F.A.C.O.G."}]),
    ("F.A.C.O.I.", [{ORTH: "F.A.C.O.I."}]),
    ("F.A.C.P.", [{ORTH: "F.A.C.P."}]),
    ("F.A.C.S.", [{ORTH: "F.A.C.S."}]),
    ("F.A.C.S.M.", [{ORTH: "F.A.C.S.M."}]),
    ("F.A.M.A.", [{ORTH: "F.A.M.A."}]),
    ("F.A.P.H.A.", [{ORTH: "F.A.P.H.A."}]),
    ("F.B.", [{ORTH: "F.B."}]),
    ("F.I.C.D.", [{ORTH: "F.I.C.D."}]),
    ("F.I.C.S.", [{ORTH: "F.I.C.S."}]),
    ("F.L.T.", [{ORTH: "F.L.T."}]),
    ("F.R.C.P.", [{ORTH: "F.R.C.P."}]),
    ("F.R.C.P.C.", [{ORTH: "F.R.C.P.C."}]),
    ("F.R.C.P.E.", [{ORTH: "F.R.C.P.E."}]),
    ("F.R.C.P.I.", [{ORTH: "F.R.C.P.I."}]),
    ("F.R.C.S.", [{ORTH: "F.R.C.S."}]),
    ("F.R.C.S.E.", [{ORTH: "F.R.C.S.E."}]),
    ("F.R.C.S.I.", [{ORTH: "F.R.C.S.I."}]),
    ("F.R.C.V.S.", [{ORTH: "F.R.C.V.S."}]),
    ("F.R.F.P.S.G.", [{ORTH: "F.R.F.P.S.G."}]),
    ("F.U.O.", [{ORTH: "F.U.O."}]),
    ("F.h.", [{ORTH: "F.h."}]),
    ("F.p.", [{ORTH: "F.p."}]),
    ("Feb.", [{ORTH: "Feb."}]),
    ("Fri.", [{ORTH: "Fri."}]),
    ("G.M.C.", [{ORTH: "G.M.C."}]),
    ("Galv.", [{ORTH: "Galv."}]),
    ("Gr.", [{ORTH: "Gr."}]),
    ("Grad.", [{ORTH: "Grad."}]),
    ("H.C.", [{ORTH: "H.C."}]),
    ("H.d.", [{ORTH: "H.d."}]),
    ("HOO.", [{ORTH: "HOO."}]),
    ("I.A.G.P.", [{ORTH: "I.A.G.P."}]),
    ("I.A.G.U.S.", [{ORTH: "I.A.G.U.S."}]),
    ("I.A.M.M.", [{ORTH: "I.A.M.M."}]),
    ("I.A.P.B.", [{ORTH: "I.A.P.B."}]),
    ("I.A.P.P.", [{ORTH: "I.A.P.P."}]),
    ("I.C.N.", [{ORTH: "I.C.N."}]),
    ("I.C.R.P.", [{ORTH: "I.C.R.P."}]),
    ("I.C.R.U.", [{ORTH: "I.C.R.U."}]),
    ("I.C.S.", [{ORTH: "I.C.S."}]),
    ("I.C.U.", [{ORTH: "I.C.U."}]),
    ("I.E.", [{ORTH: "I.E."}]),
    ("I.H.", [{ORTH: "I.H."}]),
    ("I.L.A.", [{ORTH: "I.L.A."}]),
    ("I.M.", [{ORTH: "I.M."}]),
    ("I.M.A.", [{ORTH: "I.M.A."}]),
    ("I.M.V.", [{ORTH: "I.M.V."}]),
    ("I.N.A.", [{ORTH: "I.N.A."}]),
    ("I.P.A.A.", [{ORTH: "I.P.A.A."}]),
    ("I.Q.", [{ORTH: "I.Q."}]),
    ("I.R.I.S.", [{ORTH: "I.R.I.S."}]),
    ("I.S.A.", [{ORTH: "I.S.A."}]),
    ("I.S.C.P.", [{ORTH: "I.S.C.P."}]),
    ("I.S.G.E.", [{ORTH: "I.S.G.E."}]),
    ("I.S.H.", [{ORTH: "I.S.H."}]),
    ("I.S.M.", [{ORTH: "I.S.M."}]),
    ("I.S.O.", [{ORTH: "I.S.O."}]),
    ("I.S.U.", [{ORTH: "I.S.U."}]),
    ("I.T.A.", [{ORTH: "I.T.A."}]),
    ("I.U.", [{ORTH: "I.U."}]),
    ("I.V.", [{ORTH: "I.V."}]),
    ("Inpt.", [{ORTH: "Inpt."}]),
    ("Jan.", [{ORTH: "Jan."}]),
    ("Jap.", [{ORTH: "Jap."}]),
    ("K.A.U.", [{ORTH: "K.A.U."}]),
    ("K.U.B.", [{ORTH: "K.U.B."}]),
    ("L.", [{ORTH: "L."}]),
    ("L.A.O.", [{ORTH: "L.A.O."}]),
    ("L.Ch.", [{ORTH: "L.Ch."}]),
    ("L.D.A.", [{ORTH: "L.D.A."}]),
    ("L.D.S.", [{ORTH: "L.D.S."}]),
    ("L.K.Q.C.P.I.", [{ORTH: "L.K.Q.C.P.I."}]),
    ("L.M.", [{ORTH: "L.M."}]),
    ("L.M.R.C.P.", [{ORTH: "L.M.R.C.P."}]),
    ("L.M.S.", [{ORTH: "L.M.S."}]),
    ("L.M.S.S.A.", [{ORTH: "L.M.S.S.A."}]),
    ("L.P.N.", [{ORTH: "L.P.N."}]),
    ("L.R.C.P.", [{ORTH: "L.R.C.P."}]),
    ("L.R.C.S.", [{ORTH: "L.R.C.S."}]),
    ("L.R.C.S.E.", [{ORTH: "L.R.C.S.E."}]),
    ("L.S.A.", [{ORTH: "L.S.A."}]),
    ("L.V.H.", [{ORTH: "L.V.H."}]),
    ("L.V.N.", [{ORTH: "L.V.N."}]),
    ("La.", [{ORTH: "La."}]),
    ("Lact.", [{ORTH: "Lact."}]),
    ("Lic.", [{ORTH: "Lic."}]),
    ("Linn.", [{ORTH: "Linn."}]),
    ("Lond.", [{ORTH: "Lond."}]),
    ("M.A.", [{ORTH: "M.A."}]),
    ("M.A.B.", [{ORTH: "M.A.B."}]),
    ("M.A.C.", [{ORTH: "M.A.C."}]),
    ("M.B.", [{ORTH: "M.B."}]),
    ("M.C.", [{ORTH: "M.C."}]),
    ("M.C.S.P.", [{ORTH: "M.C.S.P."}]),
    ("M.D.", [{ORTH: "M.D."}]),
    ("M.D.A.", [{ORTH: "M.D.A."}]),
    ("M.E.D.", [{ORTH: "M.E.D."}]),
    ("M.I.", [{ORTH: "M.I."}]),
    ("M.I.N.I.", [{ORTH: "M.I.N.I."}]),
    ("M.I.T.", [{ORTH: "M.I.T."}]),
    ("M.L.", [{ORTH: "M.L."}]),
    ("M.O.", [{ORTH: "M.O."}]),
    ("M.O.H.", [{ORTH: "M.O.H."}]),
    ("M.O.R.C.", [{ORTH: "M.O.R.C."}]),
    ("M.P.H.", [{ORTH: "M.P.H."}]),
    ("M.P.U.", [{ORTH: "M.P.U."}]),
    ("M.R.A.", [{ORTH: "M.R.A."}]),
    ("M.R.A.C.P.", [{ORTH: "M.R.A.C.P."}]),
    ("M.R.C.", [{ORTH: "M.R.C."}]),
    ("M.R.C.P.", [{ORTH: "M.R.C.P."}]),
    ("M.R.C.P.E.", [{ORTH: "M.R.C.P.E."}]),
    ("M.R.C.P.I.", [{ORTH: "M.R.C.P.I."}]),
    ("M.R.C.S.", [{ORTH: "M.R.C.S."}]),
    ("M.R.C.S.E.", [{ORTH: "M.R.C.S.E."}]),
    ("M.R.C.S.I.", [{ORTH: "M.R.C.S.I."}]),
    ("M.R.C.V.S.", [{ORTH: "M.R.C.V.S."}]),
    ("M.R.L.", [{ORTH: "M.R.L."}]),
    ("M.S.", [{ORTH: "M.S."}]),
    ("M.S.N.", [{ORTH: "M.S.N."}]),
    ("M.T.", [{ORTH: "M.T."}]),
    ("M.V.I.", [{ORTH: "M.V.I."}]),
    ("M.u.", [{ORTH: "M.u."}]),
    ("MSEd.", [{ORTH: "MSEd."}]),
    ("Md.", [{ORTH: "Md."}]),
    ("Merr.", [{ORTH: "Merr."}]),
    ("Mich.", [{ORTH: "Mich."}]),
    ("Mme.", [{ORTH: "Mme."}]),
    ("Mr.", [{ORTH: "Mr."}]),
    ("Mrs.", [{ORTH: "Mrs."}]),
    ("Ms.", [{ORTH: "Ms."}]),
    ("N.", [{ORTH: "N."}]),
    ("N.A.P.N.E.S.", [{ORTH: "N.A.P.N.E.S."}]),
    ("N.A.S.E.", [{ORTH: "N.A.S.E."}]),
    ("N.B.S.", [{ORTH: "N.B.S."}]),
    ("N.C.", [{ORTH: "N.C."}]),
    ("N.C.M.H.", [{ORTH: "N.C.M.H."}]),
    ("N.C.N.", [{ORTH: "N.C.N."}]),
    ("N.D.A.", [{ORTH: "N.D.A."}]),
    ("N.E.M.A.", [{ORTH: "N.E.M.A."}]),
    ("N.F.L.P.N.", [{ORTH: "N.F.L.P.N."}]),
    ("N.H.C.", [{ORTH: "N.H.C."}]),
    ("N.H.I.", [{ORTH: "N.H.I."}]),
    ("N.H.L.I.", [{ORTH: "N.H.L.I."}]),
    ("N.H.M.R.C.", [{ORTH: "N.H.M.R.C."}]),
    ("N.H.S.", [{ORTH: "N.H.S."}]),
    ("N.L.N.", [{ORTH: "N.L.N."}]),
    ("N.M.A.", [{ORTH: "N.M.A."}]),
    ("N.M.S.S.", [{ORTH: "N.M.S.S."}]),
    ("N.O.A.", [{ORTH: "N.O.A."}]),
    ("N.O.P.H.N.", [{ORTH: "N.O.P.H.N."}]),
    ("N.O.T.B.", [{ORTH: "N.O.T.B."}]),
    ("N.P.A.", [{ORTH: "N.P.A."}]),
    ("N.R.C.", [{ORTH: "N.R.C."}]),
    ("N.S.A.", [{ORTH: "N.S.A."}]),
    ("N.S.C.C.", [{ORTH: "N.S.C.C."}]),
    ("N.S.N.A.", [{ORTH: "N.S.N.A."}]),
    ("N.S.P.B.", [{ORTH: "N.S.P.B."}]),
    ("N.T.A.", [{ORTH: "N.T.A."}]),
    ("N.T.P.", [{ORTH: "N.T.P."}]),
    ("N.Y.", [{ORTH: "N.Y."}]),
    ("N.Y.D.", [{ORTH: "N.Y.D."}]),
    ("Nev.", [{ORTH: "Nev."}]),
    ("Nm.", [{ORTH: "Nm."}]),
    ("Nov.", [{ORTH: "Nov."}]),
    ("Num.", [{ORTH: "Num."}]),
    ("O.D.", [{ORTH: "O.D."}]),
    ("O.K.", [{ORTH: "O.K."}]),
    ("O.R.", [{ORTH: "O.R."}]),
    ("O.R.E.F.", [{ORTH: "O.R.E.F."}]),
    ("O.R.S.", [{ORTH: "O.R.S."}]),
    ("O.S.A.", [{ORTH: "O.S.A."}]),
    ("O.S.U.K.", [{ORTH: "O.S.U.K."}]),
    ("O.U.", [{ORTH: "O.U."}]),
    ("Ob.", [{ORTH: "Ob."}]),
    ("Oct.", [{ORTH: "Oct."}]),
    ("Oe.", [{ORTH: "Oe."}]),
    ("Ont.", [{ORTH: "Ont."}]),
    ("Ore.", [{ORTH: "Ore."}]),
    ("Outpt.", [{ORTH: "Outpt."}]),
    ("P-barb.", [{ORTH: "P-barb."}]),
    ("P.C.M.O.", [{ORTH: "P.C.M.O."}]),
    ("P.H.L.S.", [{ORTH: "P.H.L.S."}]),
    ("P.M.B.", [{ORTH: "P.M.B."}]),
    ("P.M.E.", [{ORTH: "P.M.E."}]),
    ("P.O.", [{ORTH: "P.O."}]),
    ("P.P.D.", [{ORTH: "P.P.D."}]),
    ("P.T.", [{ORTH: "P.T."}]),
    ("P.T.U.", [{ORTH: "P.T.U."}]),
    ("Ph.", [{ORTH: "Ph."}]),
    ("Ph.B.", [{ORTH: "Ph.B."}]),
    ("Ph.D.", [{ORTH: "Ph.D."}]),
    ("Ph.G.", [{ORTH: "Ph.G."}]),
    ("PhD.", [{ORTH: "PhD."}]),
    ("Ps.", [{ORTH: "Ps."}]),
    ("Pseud.", [{ORTH: "Pseud."}]),
    ("R.A.M.C.", [{ORTH: "R.A.M.C."}]),
    ("R.B.C.", [{ORTH: "R.B.C."}]),
    ("R.C.M.", [{ORTH: "R.C.M."}]),
    ("R.C.N.", [{ORTH: "R.C.N."}]),
    ("R.C.O.G.", [{ORTH: "R.C.O.G."}]),
    ("R.C.P.", [{ORTH: "R.C.P."}]),
    ("R.C.S.", [{ORTH: "R.C.S."}]),
    ("R.C.V.S.", [{ORTH: "R.C.V.S."}]),
    ("R.D.", [{ORTH: "R.D."}]),
    ("R.D.H.", [{ORTH: "R.D.H."}]),
    ("R.E.G.", [{ORTH: "R.E.G."}]),
    ("R.F.A.", [{ORTH: "R.F.A."}]),
    ("R.F.P.", [{ORTH: "R.F.P."}]),
    ("R.G.N.", [{ORTH: "R.G.N."}]),
    ("R.H.", [{ORTH: "R.H."}]),
    ("R.I.F.", [{ORTH: "R.I.F."}]),
    ("R.M.N.", [{ORTH: "R.M.N."}]),
    ("R.M.O.", [{ORTH: "R.M.O."}]),
    ("R.M.P.", [{ORTH: "R.M.P."}]),
    ("R.N.", [{ORTH: "R.N."}]),
    ("R.N.M.S.", [{ORTH: "R.N.M.S."}]),
    ("R.O.A.", [{ORTH: "R.O.A."}]),
    ("R.O.P.", [{ORTH: "R.O.P."}]),
    ("R.R.L.", [{ORTH: "R.R.L."}]),
    ("R.S.A.", [{ORTH: "R.S.A."}]),
    ("R.S.B.", [{ORTH: "R.S.B."}]),
    ("R.S.C.N.", [{ORTH: "R.S.C.N."}]),
    ("R.S.M.", [{ORTH: "R.S.M."}]),
    ("R.S.N.A.", [{ORTH: "R.S.N.A."}]),
    ("R.S.P.", [{ORTH: "R.S.P."}]),
    ("R.S.T.", [{ORTH: "R.S.T."}]),
    ("R.S.T.M.H.", [{ORTH: "R.S.T.M.H."}]),
    ("R.T.", [{ORTH: "R.T."}]),
    ("R.U.", [{ORTH: "R.U."}]),
    ("R.V.H.", [{ORTH: "R.V.H."}]),
    ("Ras.", [{ORTH: "Ras."}]),
    ("Rb.", [{ORTH: "Rb."}]),
    ("Rba.", [{ORTH: "Rba."}]),
    ("Rect.", [{ORTH: "Rect."}]),
    ("Ref.", [{ORTH: "Ref."}]),
    ("S.", [{ORTH: "S."}]),
    ("S.-G.", [{ORTH: "S.-G."}]),
    ("S.A.", [{ORTH: "S.A."}]),
    ("S.A.L.", [{ORTH: "S.A.L."}]),
    ("S.C.", [{ORTH: "S.C."}]),
    ("S.C.M.", [{ORTH: "S.C.M."}]),
    ("S.D.", [{ORTH: "S.D."}]),
    ("S.E.D.", [{ORTH: "S.E.D."}]),
    ("S.E.E.", [{ORTH: "S.E.E."}]),
    ("S.F.", [{ORTH: "S.F."}]),
    ("S.G.O.", [{ORTH: "S.G.O."}]),
    ("S.I.D.", [{ORTH: "S.I.D."}]),
    ("S.L.P.", [{ORTH: "S.L.P."}]),
    ("S.L.T.", [{ORTH: "S.L.T."}]),
    ("S.M.O.", [{ORTH: "S.M.O."}]),
    ("S.S.D.", [{ORTH: "S.S.D."}]),
    ("S.T.S.", [{ORTH: "S.T.S."}]),
    ("S.m.", [{ORTH: "S.m."}]),
    ("Sacch.", [{ORTH: "Sacch."}]),
    ("Salm.", [{ORTH: "Salm."}]),
    ("Sc.D.", [{ORTH: "Sc.D."}]),
    ("Sens.", [{ORTH: "Sens."}]),
    ("Sept.", [{ORTH: "Sept."}]),
    ("St.", [{ORTH: "St."}]),
    ("Str.", [{ORTH: "Str."}]),
    ("Strep.", [{ORTH: "Strep."}]),
    ("Strept.", [{ORTH: "Strept."}]),
    ("Subg.", [{ORTH: "Subg."}]),
    ("T.A.T.", [{ORTH: "T.A.T."}]),
    ("T.E.D.", [{ORTH: "T.E.D."}]),
    ("T.P.N.", [{ORTH: "T.P.N."}]),
    ("Tab.", [{ORTH: "Tab."}]),
    ("Tal.", [{ORTH: "Tal."}]),
    ("Tb.N.", [{ORTH: "Tb.N."}]),
    ("Tb.Sp.", [{ORTH: "Tb.Sp."}]),
    ("Tb.Th.", [{ORTH: "Tb.Th."}]),
    ("Tue.", [{ORTH: "Tue."}]),
    ("Tues.", [{ORTH: "Tues."}]),
    ("U.K.", [{ORTH: "U.K."}]),
    ("U.S.", [{ORTH: "U.S."}]),
    ("U.S.A.", [{ORTH: "U.S.A."}]),
    ("U.S.M.H.", [{ORTH: "U.S.M.H."}]),
    ("U.S.P.", [{ORTH: "U.S.P."}]),
    ("U.S.P.H.S.", [{ORTH: "U.S.P.H.S."}]),
    ("U.V.", [{ORTH: "U.V."}]),
    ("Ungt.", [{ORTH: "Ungt."}]),
    ("V.A.", [{ORTH: "V.A."}]),
    ("V.A.C.", [{ORTH: "V.A.C."}]),
    ("V.D.", [{ORTH: "V.D."}]),
    ("V.M.D.", [{ORTH: "V.M.D."}]),
    ("V.R.", [{ORTH: "V.R."}]),
    ("Va.", [{ORTH: "Va."}]),
    ("Vit.", [{ORTH: "Vit."}]),
    ("W.", [{ORTH: "W."}]),
    ("W.R.", [{ORTH: "W.R."}]),
    ("W.Va.", [{ORTH: "W.Va."}]),
    ("Wgt.", [{ORTH: "Wgt."}]),
    ("Wis.", [{ORTH: "Wis."}]),
    ("a.c.", [{ORTH: "a.c."}]),
    ("a.m.", [{ORTH: "a.m."}]),
    ("abbr.", [{ORTH: "abbr."}]),
    ("abdom.", [{ORTH: "abdom."}]),
    ("adj.", [{ORTH: "adj."}]),
    ("amp.", [{ORTH: "amp."}]),
    ("ams.", [{ORTH: "ams."}]),
    ("ant.", [{ORTH: "ant."}]),
    ("aq.", [{ORTH: "aq."}]),
    ("arb.", [{ORTH: "arb."}]),
    ("arg.", [{ORTH: "arg."}]),
    ("artif.", [{ORTH: "artif."}]),
    ("asn.", [{ORTH: "asn."}]),
    ("asst.", [{ORTH: "asst."}]),
    ("avg.", [{ORTH: "avg."}]),
    ("b.d.s.", [{ORTH: "b.d.s."}]),
    ("b.i.d.", [{ORTH: "b.i.d."}]),
    ("b.p.", [{ORTH: "b.p."}]),
    ("bilat.", [{ORTH: "bilat."}]),
    ("bk.", [{ORTH: "bk."}]),
    ("bldg.", [{ORTH: "bldg."}]),
    ("bol.", [{ORTH: "bol."}]),
    ("bull.", [{ORTH: "bull."}]),
    ("c.b.c.", [{ORTH: "c.b.c."}]),
    ("c.p.", [{ORTH: "c.p."}]),
    ("cal.", [{ORTH: "cal."}]),
    ("cap.", [{ORTH: "cap."}]),
    ("conc.", [{ORTH: "conc."}]),
    ("concn.", [{ORTH: "concn."}]),
    ("cont.", [{ORTH: "cont."}]),
    ("cor.", [{ORTH: "cor."}]),
    ("corr.", [{ORTH: "corr."}]),
    ("cpd.", [{ORTH: "cpd."}]),
    ("creat.", [{ORTH: "creat."}]),
    ("crit.", [{ORTH: "crit."}]),
    ("cu.mm.", [{ORTH: "cu.mm."}]),
    ("cx.", [{ORTH: "cx."}]),
    ("cyc.", [{ORTH: "cyc."}]),
    ("cyl.", [{ORTH: "cyl."}]),
    ("d.c.", [{ORTH: "d.c."}]),
    ("d.p.", [{ORTH: "d.p."}]),
    ("d.p.m.", [{ORTH: "d.p.m."}]),
    ("d.v.", [{ORTH: "d.v."}]),
    ("d.w.", [{ORTH: "d.w."}]),
    ("decub.", [{ORTH: "decub."}]),
    ("deg.", [{ORTH: "deg."}]),
    ("det.", [{ORTH: "det."}]),
    ("diam.", [{ORTH: "diam."}]),
    ("dir.", [{ORTH: "dir."}]),
    ("dn.", [{ORTH: "dn."}]),
    ("doc.", [{ORTH: "doc."}]),
    ("dp.", [{ORTH: "dp."}]),
    ("dr.", [{ORTH: "dr."}]),
    ("e.m.p.", [{ORTH: "e.m.p."}]),
    ("elev.", [{ORTH: "elev."}]),
    ("elix.", [{ORTH: "elix."}]),
    ("em.", [{ORTH: "em."}]),
    ("emuls.", [{ORTH: "emuls."}]),
    ("endocrinol.", [{ORTH: "endocrinol."}]),
    ("er.", [{ORTH: "er."}]),
    ("exper.", [{ORTH: "exper."}]),
    ("expt.", [{ORTH: "expt."}]),
    ("f.b.", [{ORTH: "f.b."}]),
    ("f.p.", [{ORTH: "f.p."}]),
    ("fe.", [{ORTH: "fe."}]),
    ("fig.", [{ORTH: "fig."}]),
    ("fl.", [{ORTH: "fl."}]),
    ("fld.", [{ORTH: "fld."}]),
    ("ft.", [{ORTH: "ft."}]),
    ("g-cal.", [{ORTH: "g-cal."}]),
    ("gl.", [{ORTH: "gl."}]),
    ("glu.", [{ORTH: "glu."}]),
    ("gly.", [{ORTH: "gly."}]),
    ("gm.", [{ORTH: "gm."}]),
    ("gr.", [{ORTH: "gr."}]),
    ("h.p.f.", [{ORTH: "h.p.f."}]),
    ("h.s.", [{ORTH: "h.s."}]),
    ("halluc.", [{ORTH: "halluc."}]),
    ("hct.", [{ORTH: "hct."}]),
    ("hun.", [{ORTH: "hun."}]),
    ("hyp.", [{ORTH: "hyp."}]),
    ("i.c.", [{ORTH: "i.c."}]),
    ("i.d.", [{ORTH: "i.d."}]),
    ("i.p.", [{ORTH: "i.p."}]),
    ("i.r.", [{ORTH: "i.r."}]),
    ("i.s.", [{ORTH: "i.s."}]),
    ("i.th.", [{ORTH: "i.th."}]),
    ("i.vag.", [{ORTH: "i.vag."}]),
    ("ib.", [{ORTH: "ib."}]),
    ("ibid.", [{ORTH: "ibid."}]),
    ("inj.", [{ORTH: "inj."}]),
    ("ino.", [{ORTH: "ino."}]),
    ("instr.", [{ORTH: "instr."}]),
    ("inv.", [{ORTH: "inv."}]),
    ("irreg.", [{ORTH: "irreg."}]),
    ("jour.", [{ORTH: "jour."}]),
    ("jr.", [{ORTH: "jr."}]),
    ("kc.", [{ORTH: "kc."}]),
    ("kg.-cal.", [{ORTH: "kg.-cal."}]),
    ("l.a.r.", [{ORTH: "l.a.r."}]),
    ("l.p.n.", [{ORTH: "l.p.n."}]),
    ("l.w.", [{ORTH: "l.w."}]),
    ("lam.", [{ORTH: "lam."}]),
    ("lar.", [{ORTH: "lar."}]),
    ("lb.", [{ORTH: "lb."}]),
    ("lim.", [{ORTH: "lim."}]),
    ("lin.", [{ORTH: "lin."}]),
    ("liq.", [{ORTH: "liq."}]),
    ("lo.", [{ORTH: "lo."}]),
    ("lot.", [{ORTH: "lot."}]),
    ("lys.", [{ORTH: "lys."}]),
    ("m.e.p.c.", [{ORTH: "m.e.p.c."}]),
    ("mEq.", [{ORTH: "mEq."}]),
    ("mac.", [{ORTH: "mac."}]),
    ("mech.", [{ORTH: "mech."}]),
    ("meg.", [{ORTH: "meg."}]),
    ("meq.", [{ORTH: "meq."}]),
    ("mev.", [{ORTH: "mev."}]),
    ("mi.", [{ORTH: "mi."}]),
    ("mil.", [{ORTH: "mil."}]),
    ("min.", [{ORTH: "min."}]),
    ("misc.", [{ORTH: "misc."}]),
    ("mist.", [{ORTH: "mist."}]),
    ("muc.", [{ORTH: "muc."}]),
    ("n.", [{ORTH: "n."}]),
    ("n.c.a.", [{ORTH: "n.c.a."}]),
    ("n.m.", [{ORTH: "n.m."}]),
    ("n.u.", [{ORTH: "n.u."}]),
    ("nU.", [{ORTH: "nU."}]),
    ("nat.", [{ORTH: "nat."}]),
    ("neo.", [{ORTH: "neo."}]),
    ("neu.", [{ORTH: "neu."}]),
    ("nm.", [{ORTH: "nm."}]),
    ("noct.", [{ORTH: "noct."}]),
    ("o.d.", [{ORTH: "o.d."}]),
    ("o.h.", [{ORTH: "o.h."}]),
    ("o.m.", [{ORTH: "o.m."}]),
    ("o.n.", [{ORTH: "o.n."}]),
    ("o.s.", [{ORTH: "o.s."}]),
    ("o.u.", [{ORTH: "o.u."}]),
    ("oto.", [{ORTH: "oto."}]),
    ("oz.", [{ORTH: "oz."}]),
    ("p.a.", [{ORTH: "p.a."}]),
    ("p.c.", [{ORTH: "p.c."}]),
    ("p.e.", [{ORTH: "p.e."}]),
    ("p.i.d.", [{ORTH: "p.i.d."}]),
    ("p.m.", [{ORTH: "p.m."}]),
    ("p.o.", [{ORTH: "p.o."}]),
    ("p.p.d.", [{ORTH: "p.p.d."}]),
    ("p.r.", [{ORTH: "p.r."}]),
    ("p.r.n.", [{ORTH: "p.r.n."}]),
    ("p.s.p.", [{ORTH: "p.s.p."}]),
    ("p.t.", [{ORTH: "p.t."}]),
    ("p.v.", [{ORTH: "p.v."}]),
    ("paediatr.", [{ORTH: "paediatr."}]),
    ("pediatr.", [{ORTH: "pediatr."}]),
    ("peri.", [{ORTH: "peri."}]),
    ("pkwy.", [{ORTH: "pkwy."}]),
    ("post-part.", [{ORTH: "post-part."}]),
    ("postpart.", [{ORTH: "postpart."}]),
    ("ppg.", [{ORTH: "ppg."}]),
    ("ppt.", [{ORTH: "ppt."}]),
    ("prob.", [{ORTH: "prob."}]),
    ("prof.", [{ORTH: "prof."}]),
    ("ps.p.", [{ORTH: "ps.p."}]),
    ("pulv.", [{ORTH: "pulv."}]),
    ("pur.", [{ORTH: "pur."}]),
    ("pv.", [{ORTH: "pv."}]),
    ("q.", [{ORTH: "q."}]),
    ("q.a.d.", [{ORTH: "q.a.d."}]),
    ("q.a.m.", [{ORTH: "q.a.m."}]),
    ("q.d.", [{ORTH: "q.d."}]),
    ("q.d.s.", [{ORTH: "q.d.s."}]),
    ("q.h.", [{ORTH: "q.h."}]),
    ("q.h.s.", [{ORTH: "q.h.s."}]),
    ("q.i.d.", [{ORTH: "q.i.d."}]),
    ("q.o.d.", [{ORTH: "q.o.d."}]),
    ("q.p.m.", [{ORTH: "q.p.m."}]),
    ("q.s.", [{ORTH: "q.s."}]),
    ("q.v.", [{ORTH: "q.v."}]),
    ("r.b.c.", [{ORTH: "r.b.c."}]),
    ("r.h.", [{ORTH: "r.h."}]),
    ("r.m.s.d.", [{ORTH: "r.m.s.d."}]),
    ("ra.", [{ORTH: "ra."}]),
    ("ras.", [{ORTH: "ras."}]),
    ("rec.", [{ORTH: "rec."}]),
    ("rect.", [{ORTH: "rect."}]),
    ("ref.", [{ORTH: "ref."}]),
    ("reg.", [{ORTH: "reg."}]),
    ("rehab.", [{ORTH: "rehab."}]),
    ("rep.", [{ORTH: "rep."}]),
    ("s.", [{ORTH: "s."}]),
    ("s.c.", [{ORTH: "s.c."}]),
    ("s.e.e.", [{ORTH: "s.e.e."}]),
    ("s.l.", [{ORTH: "s.l."}]),
    ("s.o.s.", [{ORTH: "s.o.s."}]),
    ("s.s.", [{ORTH: "s.s."}]),
    ("satd.", [{ORTH: "satd."}]),
    ("scr.", [{ORTH: "scr."}]),
    ("sect.", [{ORTH: "sect."}]),
    ("sed.", [{ORTH: "sed."}]),
    ("sens.", [{ORTH: "sens."}]),
    ("sep.", [{ORTH: "sep."}]),
    ("shldr.", [{ORTH: "shldr."}]),
    ("sl.", [{ORTH: "sl."}]),
    ("slt.", [{ORTH: "slt."}]),
    ("somat.", [{ORTH: "somat."}]),
    ("sp.", [{ORTH: "sp."}]),
    ("sph.", [{ORTH: "sph."}]),
    ("spp.", [{ORTH: "spp."}]),
    ("sq.", [{ORTH: "sq."}]),
    ("sr.", [{ORTH: "sr."}]),
    ("ss.", [{ORTH: "ss."}]),
    ("ssp.", [{ORTH: "ssp."}]),
    ("subfam.", [{ORTH: "subfam."}]),
    ("subg.", [{ORTH: "subg."}]),
    ("subgen.", [{ORTH: "subgen."}]),
    ("subj.", [{ORTH: "subj."}]),
    ("subsect.", [{ORTH: "subsect."}]),
    ("subsp.", [{ORTH: "subsp."}]),
    ("supp.", [{ORTH: "supp."}]),
    ("sv.", [{ORTH: "sv."}]),
    ("syr.", [{ORTH: "syr."}]),
    ("t.d.s.", [{ORTH: "t.d.s."}]),
    ("t.i.d.", [{ORTH: "t.i.d."}]),
    ("t.i.w.", [{ORTH: "t.i.w."}]),
    ("t.p.n.", [{ORTH: "t.p.n."}]),
    ("tab.", [{ORTH: "tab."}]),
    ("tal.", [{ORTH: "tal."}]),
    ("tbsp.", [{ORTH: "tbsp."}]),
    ("tens.", [{ORTH: "tens."}]),
    ("theor.", [{ORTH: "theor."}]),
    ("thromb.", [{ORTH: "thromb."}]),
    ("tinc.", [{ORTH: "tinc."}]),
    ("tinct.", [{ORTH: "tinct."}]),
    ("top.", [{ORTH: "top."}]),
    ("u.d.", [{ORTH: "u.d."}]),
    ("u.v.", [{ORTH: "u.v."}]),
    ("ung.", [{ORTH: "ung."}]),
    ("v.", [{ORTH: "v."}]),
    ("v.r.", [{ORTH: "v.r."}]),
    ("vac.", [{ORTH: "vac."}]),
    ("vd.", [{ORTH: "vd."}]),
    ("vit.", [{ORTH: "vit."}]),
    ("viz.", [{ORTH: "viz."}]),
    ("vol.", [{ORTH: "vol."}]),
    ("w.", [{ORTH: "w."}]),
    ("wgt.", [{ORTH: "wgt."}]),
    ("wt.", [{ORTH: "wt."}]),
    ("yd.", [{ORTH: "yd."}]),
    ("yr.", [{ORTH: "yr."}]),
    ("zool.", [{ORTH: "zool."}]),
    ("'s", [{ORTH: "'s"}]),
    ("&amp;", [{ORTH: "&amp;"}]),
    ("&gt;", [{ORTH: "&gt;"}]),
    ("&lt;", [{ORTH: "&lt;"}]),
    ("+/-", [{ORTH: "+/-"}]),
    ("...", [{ORTH: "..."}]),
    ("0.25%", [{ORTH: "0.25%"}]),
    ("0.50%", [{ORTH: "0.50%"}]),
    ("0.65%", [{ORTH: "0.65%"}]),
    ("0.75%", [{ORTH: "0.75%"}]),
    ("00:00:00.0", [{ORTH: "00:00:00.0"}]),
    ("6h.p.r.n.", [{ORTH: "6h.p.r.n."}]),
    ("A.", [{ORTH: "A."}]),
    ("A.FIB", [{ORTH: "A.FIB"}]),
    ("A.Fib", [{ORTH: "A.Fib"}]),
    ("A.fib", [{ORTH: "A.fib"}]),
    ("a.fib", [{ORTH: "a.fib"}]),
    ("A/P", [{ORTH: "A/P"}]),
    ("AMOXICIL...", [{ORTH: "AMOXICIL..."}]),
    ("B.", [{ORTH: "B."}]),
    ("B.I.", [{ORTH: "B.I."}]),
    ("B.I.D.", [{ORTH: "B.I.D."}]),
    ("Bilat.", [{ORTH: "Bilat."}]),
    ("c.b.i.d.", [{ORTH: "c.b.i.d."}]),
    ("c.q.1h.p.r.n.", [{ORTH: "c.q.1h.p.r.n."}]),
    ("C.", [{ORTH: "C."}]),
    ("C.Diff", [{ORTH: "C.Diff"}]),
    ("C.diff", [{ORTH: "C.diff"}]),
    ("C.difficile", [{ORTH: "C.difficile"}]),
    ("C/W", [{ORTH: "C/W"}]),
    ("D.", [{ORTH: "D."}]),
    ("D/C", [{ORTH: "D/C"}]),
    ("D/C'D", [{ORTH: "D/C'D"}]),
    ("D/c'd", [{ORTH: "D/c'd"}]),
    ("D/w", [{ORTH: "D/w"}]),
    ("DR.", [{ORTH: "DR."}]),
    ("E.", [{ORTH: "E."}]),
    ("E.C.", [{ORTH: "E.C."}]),
    ("E.C.", [{ORTH: "E.C."}]),
    ("E.C.", [{ORTH: "E.C."}]),
    ("E.COLI", [{ORTH: "E.COLI"}]),
    ("E.Coli", [{ORTH: "E.Coli"}]),
    ("E.G.", [{ORTH: "E.G."}]),
    ("E.coli", [{ORTH: "E.coli"}]),
    ("F.", [{ORTH: "F."}]),
    ("F/U", [{ORTH: "F/U"}]),
    ("G.", [{ORTH: "G."}]),
    ("H.", [{ORTH: "H."}]),
    ("H/O", [{ORTH: "H/O"}]),
    ("I.", [{ORTH: "I."}]),
    ("I.E.", [{ORTH: "I.E."}]),
    ("IMMED.", [{ORTH: "IMMED."}]),
    ("J.", [{ORTH: "J."}]),
    ("Jr.", [{ORTH: "Jr."}]),
    ("K.", [{ORTH: "K."}]),
    ("L.", [{ORTH: "L."}]),
    ("M.", [{ORTH: "M."}]),
    ("M.B.B.S.", [{ORTH: "M.B.B.S."}]),
    ("M.S.C.", [{ORTH: "M.S.C."}]),
    ("Misc.", [{ORTH: "Misc."}]),
    ("Mr.", [{ORTH: "Mr."}]),
    ("Mrs.", [{ORTH: "Mrs."}]),
    ("Ms.", [{ORTH: "Ms."}]),
    ("N.", [{ORTH: "N."}]),
    ("No.1", [{ORTH: "No.1"}]),
    ("No.2", [{ORTH: "No.2"}]),
    ("O.", [{ORTH: "O."}]),
    ("P.", [{ORTH: "P."}]),
    ("P.A.", [{ORTH: "P.A."}]),
    ("P.O.", [{ORTH: "P.O."}]),
    ("PH.D.", [{ORTH: "PH.D."}]),
    ("PULM.", [{ORTH: "PULM."}]),
    ("Pt.", [{ORTH: "Pt."}]),
    ("Q.", [{ORTH: "Q."}]),
    ("R.", [{ORTH: "R."}]),
    ("R/o'd", [{ORTH: "R/o'd"}]),
    ("REL.", [{ORTH: "REL."}]),
    ("RESP.", [{ORTH: "RESP."}]),
    ("Rd.", [{ORTH: "Rd."}]),
    ("S.", [{ORTH: "S."}]),
    ("S.O.A.R.", [{ORTH: "S.O.A.R."}]),
    ("SUSP.", [{ORTH: "SUSP."}]),
    ("SUST.", [{ORTH: "SUST."}]),
    ("Ste.", [{ORTH: "Ste."}]),
    ("T.", [{ORTH: "T."}]),
    ("TEMP.", [{ORTH: "TEMP."}]),
    ("TERM", [{ORTH: "TERM"}]),
    ("Tel.", [{ORTH: "Tel."}]),
    ("U.", [{ORTH: "U."}]),
    ("U/S", [{ORTH: "U/S"}]),
    ("V.", [{ORTH: "V."}]),
    ("VIT.", [{ORTH: "VIT."}]),
    ("X.", [{ORTH: "X."}]),
    ("Y.", [{ORTH: "Y."}]),
    ("Z.", [{ORTH: "Z."}]),
    ("a.", [{ORTH: "a."}]),
    ("a.fib", [{ORTH: "a.fib"}]),
    ("b.", [{ORTH: "b."}]),
    ("bilat.", [{ORTH: "bilat."}]),
    ("c.", [{ORTH: "c."}]),
    ("c/o", [{ORTH: "c/o"}]),
    ("c/w", [{ORTH: "c/w"}]),
    ("d/c", [{ORTH: "d/c"}]),
    ("d/c'd", [{ORTH: "d/c'd"}]),
    ("d/c'd", [{ORTH: "d/c'd"}]),
    ("d/c'ed", [{ORTH: "d/c'ed"}]),
    ("d/ced", [{ORTH: "d/ced"}]),
    ("d/t", [{ORTH: "d/t"}]),
    ("dc.", [{ORTH: "dc."}]),
    ("e.", [{ORTH: "e."}]),
    ("e.coli", [{ORTH: "e.coli"}]),
    ("e.g.", [{ORTH: "e.g."}]),
    ("etc.", [{ORTH: "etc."}]),
    ("f/u", [{ORTH: "f/u"}]),
    ("follow-up", [{ORTH: "follow-up"}]),
    ("h.", [{ORTH: "h."}]),
    ("h/o", [{ORTH: "h/o"}]),
    ("i.e.", [{ORTH: "i.e."}]),
    ("incr.", [{ORTH: "incr."}]),
    ("l.", [{ORTH: "l."}]),
    ("lbs.", [{ORTH: "lbs."}]),
    ("misc.", [{ORTH: "misc."}]),
    ("mr.", [{ORTH: "mr."}]),
    ("mrs.", [{ORTH: "mrs."}]),
    ("ms.", [{ORTH: "ms."}]),
    ("n.p.o.", [{ORTH: "n.p.o."}]),
    ("p.g.", [{ORTH: "p.g."}]),
    ("p.i.q.4h", [{ORTH: "p.i.q.4h"}]),
    ("p.o.q.4h", [{ORTH: "p.o.q.4h"}]),
    ("p.o.", [{ORTH: "p.o."}]),
    ("p.o./p.g.", [{ORTH: "p.o./p.g."}]),
    ("p.o.b.i.d.", [{ORTH: "p.o.b.i.d."}]),
    ("p.o.q.", [{ORTH: "p.o.q."}]),
    ("p.o.q.a.m.", [{ORTH: "p.o.q.a.m."}]),
    ("p.o.q.d.", [{ORTH: "p.o.q.d."}]),
    ("p.o.q.d", [{ORTH: "p.o.q.d"}]),
    ("p.o.q.p.m.", [{ORTH: "p.o.q.p.m."}]),
    ("pt.", [{ORTH: "pt."}]),
    ("pulm.", [{ORTH: "pulm."}]),
    ("q.", [{ORTH: "q."}]),
    ("q.10h.", [{ORTH: "q.10h."}]),
    ("q.11h.", [{ORTH: "q.11h."}]),
    ("q.12h.", [{ORTH: "q.12h."}]),
    ("q.13h.", [{ORTH: "q.13h."}]),
    ("q.14h.", [{ORTH: "q.14h."}]),
    ("q.15h.", [{ORTH: "q.15h."}]),
    ("q.16h.", [{ORTH: "q.16h."}]),
    ("q.1h.", [{ORTH: "q.1h."}]),
    ("q.24", [{ORTH: "q.24"}]),
    ("q.24h", [{ORTH: "q.24h"}]),
    ("q.24h.", [{ORTH: "q.24h."}]),
    ("q.2h.", [{ORTH: "q.2h."}]),
    ("q.3h.", [{ORTH: "q.3h."}]),
    ("q.4 h.", [{ORTH: "q.4 h."}]),
    ("q.4-6h", [{ORTH: "q.4-6h"}]),
    ("q.48", [{ORTH: "q.48"}]),
    ("q.4h.", [{ORTH: "q.4h."}]),
    ("q.4.h.", [{ORTH: "q.4.h."}]),
    ("q.5h.", [{ORTH: "q.5h."}]),
    ("q.5.h.", [{ORTH: "q.5.h."}]),
    ("q.6h.", [{ORTH: "q.6h."}]),
    ("q.6.h.", [{ORTH: "q.6.h."}]),
    ("q.7h.", [{ORTH: "q.7h."}]),
    ("q.7.h.", [{ORTH: "q.7.h."}]),
    ("q.8h.", [{ORTH: "q.8h."}]),
    ("q.8.h.", [{ORTH: "q.8.h."}]),
    ("q.9h.", [{ORTH: "q.9h."}]),
    ("q.9.h.", [{ORTH: "q.9.h."}]),
    ("q.a.c.", [{ORTH: "q.a.c."}]),
    ("q.a.m.", [{ORTH: "q.a.m."}]),
    ("q.d.", [{ORTH: "q.d."}]),
    ("q.day", [{ORTH: "q.day"}]),
    ("q.eight", [{ORTH: "q.eight"}]),
    ("q.five", [{ORTH: "q.five"}]),
    ("q.four", [{ORTH: "q.four"}]),
    ("q.nine", [{ORTH: "q.nine"}]),
    ("q.one", [{ORTH: "q.one"}]),
    ("q.p.m.", [{ORTH: "q.p.m."}]),
    ("q.seven", [{ORTH: "q.seven"}]),
    ("q.six", [{ORTH: "q.six"}]),
    ("q.three", [{ORTH: "q.three"}]),
    ("q.two", [{ORTH: "q.two"}]),
    ("r.", [{ORTH: "r."}]),
    ("r/o", [{ORTH: "r/o"}]),
    ("r/r/w", [{ORTH: "r/r/w"}]),
    ("resp.", [{ORTH: "resp."}]),
    ("s.c.b.i.d.", [{ORTH: "s.c.b.i.d."}]),
    ("s.c.q.1h.p.r.n", [{ORTH: "s.c.q.1h.p.r.n"}]),
    ("s/p", [{ORTH: "s/p"}]),
    ("S/P", [{ORTH: "S/P"}]),
    ("sat.", [{ORTH: "sat."}]),
    ("tel.", [{ORTH: "tel."}]),
    ("temp.", [{ORTH: "temp."}]),
    ("vs.", [{ORTH: "vs."}]),
    ("w/", [{ORTH: "w/"}]),
    ("W/O", [{ORTH: "W/O"}]),
    ("x-ray", [{ORTH: "x-ray"}]),
    ("y/o", [{ORTH: "y/o"}]),
    ("y.o", [{ORTH: "y.o"}]),
    ("y.o.", [{ORTH: "y.o."}]),
]


def build_token_match_rgx():
    """
    Build accept & reject patterns for individual tokens. Preserving certain
    token groupings (e.g., lab values) is useful for preventing false positives
    during sentence boundary detection.

    :return:
    """
    # accept tokenization
    include_rgx = [
        r"""^[(][0-9]""",  # ignore some head/tail punctuation cases with leading paranthesis
        r"""[/][0-9]+[,]$""",
        r"""[0-9]+[/][0-9]+[.,]$""",  # fix dates with trailing punctuation: 01/01/2001,
    ]

    # override tokenization
    exclude_rgx = [
        r"""^[0-9]{1,3}[.][0-9]{1,2}[/][0-9]{1,3}[.][0-9]{1,2}$""",  # ratio of floats: 0.3/0.7
        r"""^[-]*[0-9]{1,3}[.][0-9]{1,4}$""",  # 100.02 -1.002
        r"""^([0-9]{3}[.]){2}[0-9]{4}$""",  # Phone numbers, 555.555.5555
        r"""^[A-Z]*[0-9]+[.][0-9A-Z]+$""",  # ICD9 codes: 136.9BJ
        r"""^[0-9]+[.][0-9]+([%]|mm|cm|mg|ml)$""",  # measurement 1.0mm
        r"""[0-9]+[.][0-9]+[-][0-9]+[.][0-9]+""",  # ignore range/intervals 0.1-0.4 mg
        r"""^[0-9]+[.][0-9]+$""",
        r"""^([A-Z][\.]|[1-9][0-9]*[\.)])$"""  # list item or single letter (often middle initial)
        r"""[0-9]+[/][0-9]+""",  # fractions, blood pressure readings, etc.: 1/2 120/80
        # r'''^[A-Za-z][/][A-Za-z]([/][A-Za-z])*$''', # skip abbreviations of the form: n/v, c/d/i
        # date time expressions
        r"""([01][0-9]/[0-3][0-9])""",  # 11/12
        r"""[0-1]{0,1}[0-9][/]([3][01]|[12][0-9]|[0-9])[/]((19|20)[0-9]{2}|[0-3][0-9])\b""",  # 1/11/2000
        r"""http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+""",  # URL
        r"""^([0-9]{1,2}|[A-Z])[).]$""",  # List items: 1. 1) A.
        r"""[0-2][0-9][:][0-9]{2}[:][0-9]{2}[.][0-9]""",  # times 11:09:00.0
        # lab values
        r"""[A-Za-z()]+[-<]{1,2}[0-9]{1,2}[.][0-9]{1,2}[*#]{0,2}""",  # cTropnT-<0.01 |  HCT-26.7*  | INR(PT)-1.3
        r"""([0-9]+[-][0-9]+[-][0-9]+)|([0-9]+[-][0-9]+)""",  # dates
    ]

    return re.compile("|".join(include_rgx)), re.compile("|".join(exclude_rgx))


def token_match(s, include_rgx, exclude_rgx):
    if include_rgx.search(s):
        return False
    elif exclude_rgx.search(s):
        return True
    return False


def ct_tokenizer(nlp):
    """
    Clinical Note Tokenizer

    - Keep prefix/suffix/infix regexes as simple as possible
    - Move token complexity to special cases when possible
    - token_match exceptions are can be *order dependant* so use caution

    """
    prefix_re = re.compile(r"""^([\["'()*+-?/<>#%]+|[><][=])+""")
    suffix_re = re.compile(r"""([\]"'),-.:;*]|'s)$""")
    infix_re = re.compile(r"""[%(),-./;=?]+""")

    include_rgx, exclude_rgx = build_token_match_rgx()
    f_token_match = functools.partial(
        token_match, include_rgx=include_rgx, exclude_rgx=exclude_rgx
    )

    tokenizer = Tokenizer(
        nlp.vocab,
        prefix_search=prefix_re.search,
        suffix_search=suffix_re.search,
        infix_finditer=infix_re.finditer,
        token_match=f_token_match,
    )

    for term, attrib in special_cases:
        tokenizer.add_special_case(term, attrib)

    return tokenizer