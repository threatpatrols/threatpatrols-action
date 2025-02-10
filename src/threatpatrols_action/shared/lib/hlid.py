from datetime import datetime, timezone
from uuid import uuid4


class HLID:
    """
    A human-readable twist on ULID/UUID values; A universally unique human-time-lexicographically sortable
    identifier using the same form as a UUID4 which makes it possible to use with existing UUID4 systems
    such as database storage and validators.

      20241105-1108-0052-0000-8fa646f09a7e
      ^        ^    ^    ^    ^
      |        |    |    |    | nonce-value
      |        |    |    | milliseconds
      |        |    | seconds (zero padded with 2x zeros)
      |        | hours and minutes
      | year and month and day

    HLID example:     20241105-0153-0041-0874-67961ce919d7
    UUID4 comparison: 1c21583a-9b17-11ef-99e9-d34117a8d86d

    :return: str
    """

    _value: str

    def __init__(self):
        ts = datetime.now(timezone.utc)
        nonce = str(uuid4()).split("-")[-1]
        self._value = f"{ts.strftime('%Y%m%d-%H%M-00%S')}-{ts.strftime("%f")[0:4]}-{nonce}"

    def __call__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"HLID({self._value})"

    def __str__(self) -> str:
        return self._value

    @property
    def datetime(self) -> datetime:
        """
        Returns a datetime object of the date-and-time that the HLID represents
        :return: datetime
        """
        return datetime(
            year=int(self._value[0:4]),
            month=int(self._value[4:6]),
            day=int(self._value[6:8]),
            hour=int(self._value[9:11]),
            minute=int(self._value[11:13]),
            second=int(self._value[16:18]),
            microsecond=int(self._value[19:23]) * 100,
            tzinfo=timezone.utc,
        )

    @property
    def age(self) -> float:
        return (datetime.now(timezone.utc) - self.datetime).total_seconds()


def hlid() -> HLID:
    return HLID()
