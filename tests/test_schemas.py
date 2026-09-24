from mira.schemas import AssociatedDisease


def test_associated_disease_fields_are_optional() -> None:
    disease = AssociatedDisease()

    assert disease.diseaseFromSource is None
    assert disease.diseaseId is None
