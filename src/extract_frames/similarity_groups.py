from extract_frames.models import ImageHashRecord, SimilarityGroup


def group_similar_images(
    records: list[ImageHashRecord],
    threshold: int,
    include_singletons: bool = False,
) -> list[SimilarityGroup]:
    successful_records = sorted(
        (record for record in records if record.success and record.hash_value is not None),
        key=lambda record: record.image_path.as_posix(),
    )
    parent: dict[int, int] = {index: index for index in range(len(successful_records))}

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first_index: int, second_index: int) -> None:
        first_parent = find(first_index)
        second_parent = find(second_index)
        if first_parent != second_parent:
            parent[second_parent] = first_parent

    for first_index, first_record in enumerate(successful_records):
        for second_index in range(first_index + 1, len(successful_records)):
            second_record = successful_records[second_index]
            distance = first_record.hash_value - second_record.hash_value
            if distance <= threshold:
                union(first_index, second_index)

    grouped_indexes: dict[int, list[int]] = {}
    for index in range(len(successful_records)):
        grouped_indexes.setdefault(find(index), []).append(index)

    groups: list[SimilarityGroup] = []
    for indexes in grouped_indexes.values():
        if len(indexes) == 1 and not include_singletons:
            continue
        image_paths = tuple(successful_records[index].image_path for index in indexes)
        groups.append(
            SimilarityGroup(
                group_id=len(groups) + 1,
                representative_path=image_paths[0],
                image_paths=image_paths,
            )
        )

    return groups