import hashlib

from scripts.build_aegis_manifest import calculate_sha256


def test_sha256_changes_when_dataset_changes(tmp_path):
    original = tmp_path / "dataset.json"
    modified = tmp_path / "dataset_modified.json"

    original.write_text(
        '{"incident_id":"INC-001","severity":"high"}',
        encoding="utf-8",
    )

    modified.write_text(
        '{"incident_id":"INC-001","severity":"critical"}',
        encoding="utf-8",
    )

    original_hash = calculate_sha256(original)
    modified_hash = calculate_sha256(modified)

    assert original_hash != modified_hash


def test_sha256_is_deterministic(tmp_path):
    dataset = tmp_path / "dataset.json"

    dataset.write_text(
        '{"incident_id":"INC-001","severity":"high"}',
        encoding="utf-8",
    )

    first_hash = calculate_sha256(dataset)
    second_hash = calculate_sha256(dataset)

    assert first_hash == second_hash
    assert len(first_hash) == 64