import json
import random


def DiagnoseImage(ImagePath, ImageType):
    DiagJSON = dict()
    DiagBoxes = dict()
    chest_diseases = ["Pneumonia", "PneumoThorax",
                      "Infusion", "CardioMegaly", "Nodule", "Bronchitis"]
    breast_diseases = ["Calcification", "Circumscribed",
                       "Spiculated", "Ill-defined", "Distortion", "Asymmetry"]
    retina_diseases = ["Macular Degeneration", "Melanoma - Cancer", "Diabetic Retinopathy",
                       "Glaucoma", "Hypertension", "Bronchitis"]
    c = random.sample(range(20, 79), 6)

    if ImageType == "ChestX-Ray":
        for i in range(len(c)):
            DiagJSON[chest_diseases[i]] = c[i]/100

    if ImageType == "BreastCancer":
        for i in range(len(c)):
            DiagJSON[breast_diseases[i]] = c[i]/100

    if ImageType == "RetinaImage":
        for i in range(len(c)):
            DiagJSON[retina_diseases[i]] = c[i]/100

    return json.dumps(DiagJSON), json.dumps(DiagBoxes)
