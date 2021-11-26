import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, List, Optional, Callable, Dict, Union, Sequence, Tuple

from led_machine.percent import ReversingPercentGetter
from led_machine.blend import AlterBlend
from led_machine.partition import AlterPartition
from led_machine.alter import Alter, AlterNothing, AlterMultiplexer, Position
from led_machine.parse import StaticToken, Token, StringToken, OrganizerToken, NothingToken

PARTITION_TOKEN = StaticToken("partition", "|")
BLEND_TOKEN = StaticToken("blend", "~")


class Length(ABC):
    def __init__(self):
        pass


class PixelLength(Length):
    def __init__(self, pixel_length: int):
        super().__init__()
        self.pixel_length: Final[int] = pixel_length
        if pixel_length < 0:
            raise ValueError(f"Pixel length cannot be negative! pixel_length: {pixel_length}")


class PercentLength(Length):
    def __init__(self, percent: float):
        super().__init__()
        self.percent: Final[float] = percent
        if percent < 0:
            raise ValueError(f"Percent cannot be less than 0! percent: {percent}")
        if percent > 1:
            raise ValueError(f"Percent cannot be greater than 1! percent: {percent}")


@dataclass
class CreatorData:
    has_color: bool
    has_pattern: bool

    preferred_length: Union[None, PixelLength, PercentLength] = None


class AlterCreator(ABC):
    def __init__(self, creator_data: CreatorData):
        self.creator_data: Final[CreatorData] = creator_data

    @abstractmethod
    def create(self, start_pixel: int, pixel_count: int, wrap_at: int, wrap_to: int) -> Alter:
        pass


class StaticCreator(AlterCreator):
    def __init__(self, creator_data: CreatorData, alter: Alter):
        super().__init__(creator_data)
        self.alter = alter

    def create(self, start_pixel: int, pixel_count: int, wrap_at: int, wrap_to: int) -> Alter:
        return self.alter


NOTHING_CREATOR = StaticCreator(CreatorData(False, False), AlterNothing())


class CombinerCreator(AlterCreator):
    def __init__(self, color_creators: List[AlterCreator], pattern_creators: List[AlterCreator]):
        super().__init__(CreatorData(bool(color_creators), bool(pattern_creators)))
        self.color_creators = color_creators
        self.pattern_creators = pattern_creators

    def create(self, start_pixel: int, pixel_count: int, wrap_at: int, wrap_to: int) -> Alter:
        color_alters = [creator.create(start_pixel, pixel_count, wrap_at, wrap_to) for creator in self.color_creators]
        pattern_alters = [creator.create(start_pixel, pixel_count, wrap_at, wrap_to) for creator in self.pattern_creators]
        return AlterMultiplexer(color_alters + pattern_alters)


class PartitionAlterCreator(AlterCreator):
    def __init__(self, creators: List[AlterCreator], partition_offset: int):
        super().__init__(CreatorData(
            any(creator.creator_data.has_color for creator in creators),
            any(creator.creator_data.has_pattern for creator in creators)
        ))
        self.creators = creators
        self.partition_offset = partition_offset

    def create(self, start_pixel: int, pixel_count: int, wrap_at: int, wrap_to: int) -> Alter:
        # TODO use preferred_length
        pixels_per_partition = pixel_count // len(self.creators)
        extra_pixels = pixel_count % len(self.creators)
        start_pixel = start_pixel + self.partition_offset
        if start_pixel > wrap_at:
            start_pixel += -wrap_at + wrap_to
        override_list = []
        for i, creator in enumerate(self.creators):
            length = pixels_per_partition + (1 if i < extra_pixels else 0)
            end_pixel = start_pixel + length - 1  # The index of the last pixel in this partition
            partitions: List[Tuple[Position, Position]] = []
            if end_pixel >= wrap_at:
                end_length = wrap_at - start_pixel  # the length to get to the end *before* wrapping
                leftover_length = length - end_length  # the length of the partition that wrapped
                partitions.append((start_pixel, end_length))
                partitions.append((wrap_to, leftover_length))
                alter = creator.create(start_pixel, length, wrap_at, wrap_to)
                start_pixel = wrap_to + leftover_length
            else:
                partitions.append((start_pixel, length))
                alter = creator.create(start_pixel, length, start_pixel + length, start_pixel)
                start_pixel += length
                if start_pixel >= wrap_at:
                    start_pixel += -wrap_at + wrap_to
            override_list.append((alter, partitions))

        return AlterPartition(override_list)


class BlendAlterCreator(AlterCreator):
    def __init__(self, creators: List[AlterCreator]):
        super().__init__(CreatorData(
            any(creator.creator_data.has_color for creator in creators),
            any(creator.creator_data.has_pattern for creator in creators)
        ))
        self.creators = creators

    def create(self, start_pixel: int, pixel_count: int, wrap_at: int, wrap_to: int) -> Alter:
        alters = [creator.create(start_pixel, pixel_count, wrap_at, wrap_to) for creator in self.creators]
        default_percent_getter = ReversingPercentGetter(2.0, 10.0 * 60, 2.0)  # TODO don't hard code speed
        return AlterBlend(default_percent_getter, alters)


@dataclass
class CreatorSettings:
    pixel_offsets: Dict[str, int]
    current_partition_offset: int
    """The current partition offset. This should first be initialized to the default partition offset, then it may be changed explicitly."""

    def get_offset(self, offset_string: str) -> Optional[int]:
        try:
            return int(offset_string)
        except ValueError:
            return self.pixel_offsets.get(offset_string)


def get_string_after(text: str, target_text: str) -> Optional[str]:
    split = text.split()
    previous_element: Optional[str] = None
    for element in split:
        if previous_element == target_text:
            return element
        previous_element = element
    return None


def get_number_before(text: str, target_text: str) -> Optional[float]:
    split = text.split()
    previous_element: Optional[str] = None
    for element in split:
        if previous_element is not None and element == target_text:
            try:
                return float(previous_element)
            except ValueError:
                pass
        previous_element = element
    return None


def __split_tokens(tokens: List[Token], split_on: Token) -> List[List[Token]]:
    r = []
    current = []
    for token in tokens:
        if token == split_on:
            r.append(current)
            current = []
        else:
            current.append(token)

    r.append(current)
    return r


def tokens_to_creator(
    tokens: List[Token],
    text_to_color_alter: Callable[[str], Optional[Alter]],
    text_to_pattern_alter: Callable[[str], Optional[Alter]],
    creator_settings: CreatorSettings
) -> Optional[AlterCreator]:
    blended_token_list = __split_tokens(tokens, BLEND_TOKEN)  # split on the blend ("~") token first
    if len(blended_token_list) <= 1:
        assert len(blended_token_list) != 0, "__split_tokens should always at least give us a length of 1!"
        # there's nothing to blend, so maybe this is our "base case"
        tokens = blended_token_list[0]
        partition_token_list = __split_tokens(tokens, PARTITION_TOKEN)
        if len(partition_token_list) <= 1:
            assert len(partition_token_list) != 0, "__split_tokens should always at least give us a length of 1!"
            # There are no partitions, so this is truly our "base case"
            tokens = partition_token_list[0]
            for token in tokens:
                if isinstance(token, StringToken):
                    # See if there's an explicitly defined offset that we will make "default" before we add creators to creators_to_combine
                    offset_string = get_string_after(token.data, "offset")
                    if offset_string is not None:
                        new_offset = creator_settings.get_offset(offset_string)
                        if new_offset is not None:
                            creator_settings = dataclasses.replace(
                                creator_settings,
                                current_partition_offset=new_offset
                            )

            creators_to_combine = []
            for token in tokens:
                if isinstance(token, StringToken):
                    color_alter = text_to_color_alter(token.data)
                    pattern_alter = text_to_pattern_alter(token.data)
                    if color_alter is not None:
                        creators_to_combine.append(StaticCreator(CreatorData(True, False), color_alter))
                    if pattern_alter is not None:
                        creators_to_combine.append(StaticCreator(CreatorData(False, True), pattern_alter))
                elif isinstance(token, OrganizerToken):
                    creator = tokens_to_creator(
                        token.tokens, text_to_color_alter, text_to_pattern_alter,
                        dataclasses.replace(creator_settings, current_partition_offset=0)
                    )
                    creators_to_combine.append(creator)
                elif isinstance(token, StaticToken):
                    print(f"Unknown static token: {token}")  # TODO make some sort of error reporting mechanism
                elif not isinstance(token, NothingToken):
                    print(f"Unknown token: {token}")
            color_creators = []  # has creators with has_color=True
            pattern_creators = []  # has creators with has_color=False
            for creator in creators_to_combine:
                if creator.creator_data.has_color:
                    color_creators.append(creator)
                else:
                    pattern_creators.append(creator)
            return CombinerCreator(color_creators, pattern_creators)
        else:  # This is our case for partitioning
            creators_to_partition = []
            for token_list in partition_token_list:
                creator = tokens_to_creator(token_list, text_to_color_alter, text_to_pattern_alter, creator_settings)
                creators_to_partition.append(creator or NOTHING_CREATOR)
            return PartitionAlterCreator(creators_to_partition, creator_settings.current_partition_offset)
    else:  # This is the case for blending
        creators_to_blend = []
        for token_list in blended_token_list:
            creator = tokens_to_creator(token_list, text_to_color_alter, text_to_pattern_alter, creator_settings)
            creators_to_blend.append(creator or NOTHING_CREATOR)

        return BlendAlterCreator(creators_to_blend)
