from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from copy import deepcopy
from itertools import product
from functools import reduce
from numbers import Number
from typing import Any, Callable, Generator, Iterable, List, Tuple, TypeVar, Union


T = TypeVar('T', bound='Parent')


class NestedDict(MutableMapping):
    """
    Nested dictionary.

    Handle nested dictionaries using an interface
    similar to standard dictionaries.
    For most operations, a NestedDict behaves
    like a nested dictionary that was flattened.

    Args:
        dictionary (dict): Input nested dictionary.
        copy (bool): Set to True to copy the input dictionary.

    See Also:
        NestedDict.from_product : Initialize from cartesian product.

        NestedDict.from_tuples : Initialize from list of tuples.

    Examples:
        Initialize from a nested dictionary.

        >>> d = {"a": {"a": 0, "b": 1}, "b": 2}
        >>> nd = NestedDict(d)
        >>> nd
        NestedDict({'a': {'a': 0, 'b': 1}, 'b': 2})

        Get an item.

        >>> nd["a"]
        {'a': 0, 'b': 1}
        >>> nd[("a", "b")]
        1

        Set an item.

        >>> nd[("c", "a")] = 3
        >>> nd
        NestedDict({'a': {'a': 0, 'b': 1}, 'b': 2, 'c': {'a': 3}})

        Delete an item.

        >>> del nd["c"]
        >>> nd
        NestedDict({'a': {'a': 0, 'b': 1}, 'b': 2})

        Iterate over keys.

        >>> [key for key in nd]
        [('a', 'a'), ('a', 'b'), ('b',)]
        >>> [key for key in nd.keys()]
        [('a', 'a'), ('a', 'b'), ('b',)]

        Iterate over values.

        >>> [value for value in nd.values()]
        [0, 1, 2]

        Iterate over items.

        >>> [item for item in nd.items()]
        [(('a', 'a'), 0), (('a', 'b'), 1), (('b',), 2)]
    """

    @classmethod
    def from_product(cls, *keys: List[Iterable], value: Any = None) -> T:
        """
        Initialize a NestedDict from the cartesian product of the keys.

        A common value can be assigned to all keys.

        Args:
            *keys: Each iterable.
            value: Value assigned to all keys.

        Returns:
            NestedDict

        Examples:
            >>> keys = [("A", "B"), ("a", "b")]
            >>> NestedDict.from_product(*keys)
            NestedDict({'A': {'a': None, 'b': None}, 'B': {'a': None, 'b': None}})

            Initialize with a different value.

            >>> NestedDict.from_product(*keys, value=0)
            NestedDict({'A': {'a': 0, 'b': 0}, 'B': {'a': 0, 'b': 0}})
        """
        instance = cls()
        for key in product(*keys):
            instance[key] = value
        return instance

    @classmethod
    def from_tuples(cls, *tuples: List[Iterable], value: Any = None) -> T:
        """
        Initialize a NestedDict from a list of iterables.

        A common value can be assigned to all keys.

        Args:
            tuples: Tuples corresponding to the keys of the NestedDict.
            value: Value assigned to all keys.

        Returns:
            NestedDict

        Examples:
            >>> tuples = [("a", "aa"), ("b",)]
            >>> NestedDict.from_tuples(*tuples)
            NestedDict({'a': {'aa': None}, 'b': None})

            Initialize with a different value.

            >>> NestedDict.from_tuples(*tuples, value=0)
            NestedDict({'a': {'aa': 0}, 'b': 0})
        """
        ndict = cls()
        for tuple in tuples:
            ndict[tuple] = value
        return ndict

    def __init__(self, dictionary: dict = None, copy: bool = False) -> None:
        """
        Initialize a NestedDict from a dictionary.
        
        See class docstring.
        """
        if dictionary is None:
            dictionary = {}
        self._ndict = deepcopy(dictionary) if copy else dictionary

    def __getitem__(self, key: Union[Any, Tuple[Any]]) -> Any:
        """
        Get item associated to the key.

        Args:
            key:
                Either comma-separated values or tuples.

        Returns:
            Item associated to the key.

        Raises:
            KeyError: If the key does not belong to the NestedDict.

        Examples:
            >>> d = {"a": {"a": 0, "b": 1}}
            >>> nd = NestedDict(d)

            Get the first level.

            >>> nd["a"]
            {'a': 0, 'b': 1}

            Get a deeper value.

            >>> nd["a", "a"]
            0

            Tuples can be passed too.
            >>> nd[("a", "b")]
            1

            An exception is thrown if they key does not exist.

            >>> nd["z"]
            Traceback (most recent call last):
            ...
            KeyError: ('z',)
        """
        if not isinstance(key, tuple):
            key = (key,)
        item = self._ndict

        for k in key:
            try:
                item = item[k]
            except KeyError:
                raise KeyError(key)
            except TypeError:
                raise KeyError(key)
        return item

    def __setitem__(self, key: Union[Any, Tuple[Any]], value: Any) -> None:
        """
        Set the key to the given value.

        If the key does not exist it is created.

        Args:
            key: Key to be set.
            value: New value for the key.

        Examples:
            Set an existing key.

            >>> nd = NestedDict({"a": {"aa": 0}})
            >>> nd["a", "aa"] = 1
            >>> nd
            NestedDict({'a': {'aa': 1}})

            Set a new key.
            >>> nd["a", "ab"] = 2
            >>> nd
            NestedDict({'a': {'aa': 1, 'ab': 2}})
        """
        if not isinstance(key, tuple):
            key = (key,)
        item = self._ndict
        for k in key[:-1]:
            item = item.setdefault(k, {})
        item[key[-1]] = value

    def __delitem__(self, key: Union[Any, Tuple[Any]]) -> None:
        """
        Delete item corresponding to the key.

        If the levels above are left empty, they are deleted.

        Args:
            key: Key as defined in NestedDict.__getitem__

        Examples:
            >>> d = {"a": {"aa": {"aaa": 0}}, "b": 1}
            >>> nd = NestedDict(d)
            >>> del nd["b"]
            >>> nd
            NestedDict({'a': {'aa': {'aaa': 0}}})

            Levels which are left empty after deleting an item
            are deleted too.

            >>> del nd["a", "aa", "aaa"]
            >>> nd
            NestedDict({})
        """
        if not isinstance(key, tuple):
            key = (key,)
        new_key, last_key = key[:-1], key[-1]
        del self[new_key][last_key]

        if (new_key != ()) & (self[new_key] == {}):
            self.__delitem__(new_key)

    def __iter__(self) -> Generator:
        """
        Iterate over a NestedDict.

        Yield only the keys that are associated to a leaf value.

        Examples:
            >>> d = {"a": {"aa": 0, "ab": 1}, "b": 2}
            >>> nd = NestedDict(d)
            >>> [key for key in nd]
            [('a', 'aa'), ('a', 'ab'), ('b',)]
        """
        def wrapped(ndict, key=[]):
            """Traverse the nested dictionary recursively,
            yield the key once a leaf value is reached."""
            if not isinstance(ndict, dict):
                yield tuple(key)
            else:
                for node, branch in ndict.items():
                    key.append(node)
                    yield from wrapped(branch, key)
                    key.pop()

        return wrapped(self._ndict)

    def __len__(self) -> int:
        """
        Number of leaf values.

        Examples:
            >>> nd = NestedDict({"a": {"aa": 0, "ab": 0}, "b": 0})
            >>> len(nd)
            3
        """
        length = 0
        for _ in self:
            length += 1
        return length

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self._ndict})"

    @property
    def extract(self):
        """Extract item as a NestedDict."""
        return _Extractor(self)

    def copy(self) -> T:
        """Return a deep copy."""
        return deepcopy(self)

    def to_dict(self):
        """Return a copy as a dictionary."""
        return deepcopy(self._ndict)


class _Extractor:
    """Class that allows methods of other classes to have square brackets"""

    def __init__(self, extractee):
        self._extractee = extractee

    def __getitem__(self, key):
        """Where _extractee would only return the value for a given key,
        this method returns a new _exctractee instance including the key as well.

        An empty string means all keys are chosen"""
        if type(key) is not tuple:
            key = (key,)
        item = self._extractee.__class__()

        if "" in key:
            for self_key in self._extractee.keys():
                if len(self_key) < len(key):
                    continue
                for k, s_k in zip(key, self_key):
                    if k == "":
                        continue
                    elif k != s_k:
                        break
                else:
                    item[self_key] = self._extractee[self_key]
        else:
            item[key] = self._extractee[key]

        return item


class _Arithmetics(ABC):
    """
    Mixin class providing methods for arithmetic operations.
    Useful when all operations share the same base mechanism.
    """

    @abstractmethod
    def _arithmetic_operation(
        self, other, operation: str = "__add__", symbol: str = "+"
    ):
        """General implementation of any arithmetic operation, just pass the operation and symbol
        Once this is defined all methods below should work"""
        raise NotImplementedError

    def __add__(self, other):
        return self._arithmetic_operation(other, "__add__", "+")

    def __sub__(self, other):
        return self._arithmetic_operation(other, "__sub__", "-")

    def __mul__(self, other):
        return self._arithmetic_operation(other, "__mul__", "*")

    def __truediv__(self, other):
        return self._arithmetic_operation(other, "__truediv__", "/")

    def __floordiv__(self, other):
        return self._arithmetic_operation(other, "__floordiv__", "//")

    def __mod__(self, other):
        return self._arithmetic_operation(other, "__mod__", "%")

    def __pow__(self, other):
        return self._arithmetic_operation(other, "__pow__", "**")

    def __neg__(self):
        return self * -1


class DataDict(NestedDict, _Arithmetics):
    """A NestedDict that supports arithmetics.
    Other methods are included that make DataDict similar to DataFrames"""

    def _arithmetic_operation(self, other, operation: str, symbol: str):
        """Implements any arithmetic operation, just pass the underlying method as string
        The symbol, passed as a string, will appear in the exception message if any
        The operation is performed only between NestedProperties or with numbers"""
        result = self.copy()
        if isinstance(other, self.__class__):
            for other_key, other_value in other.items():
                if other_key in self:
                    for key, value in self.extract[other_key].items():
                        result[key] = getattr(value, operation).__call__(other_value)
                else:
                    raise TypeError(
                        f"unsupported operand type(s) for {symbol}: incompatible keys"
                    )
            return result

        elif isinstance(other, Number):
            for key, value in self.items():
                result[key] = getattr(value, operation).__call__(other)
            return result

        return TypeError(
            f"unsupported operand type(s) for {symbol}: {type(self)} and {type(other)}"
        )

    def apply(self, func: Callable, inplace: bool = False):
        """Apply func to all values"""
        if inplace:
            for key, leaf in self.items():
                self[key] = func(leaf)
        else:
            new_self = self.copy()
            for key, leaf in new_self.items():
                new_self[key] = func(leaf)
            return new_self

    def reduce(self, func: Callable, *initial: Any):
        """Pass func and initial to functools.reduce and apply it to all values"""
        return reduce(func, self.values(), *initial)

    def total(self):
        """Returns sum of all values"""
        return sum(self.values())

    def mean(self) -> Number:
        """Returns mean of all values"""
        return self.total() / len(self)

    def std(self) -> Number:
        """Returns standard deviation of all values"""
        step = self.reduce(lambda a, b: a + (b - self.mean()) ** 2, 0)
        step /= len(self) - 1
        return step**0.5


if __name__ == "__main__":

    farm_data = {
        "T1": {
            "blade": {"Mx": 10, "My": 0.9, "Mz": 2},
            "tower": {"Mx": 4, "My": 0.85, "Mz": 3},
        },
        "T2": {
            "tower": {"Mx": 4, "My": 0.0, "Mz": 4},
            "gearbox": {
                "Mx": {"sensor_1": 2, "sensor_2": 1},
                "My": {"sensor_1": 2, "sensor_2": 1},
            },
        },
    }

    # Initialize class from a nested dictionary
    farm = NestedProperty(farm_data)

    # Use CartesianInit to initialise from lists
    turbines = ["T" + str(i) for i in range(1, 11)]
    components = ["blade", "tower", "gearbox"]
    loads = ["Mx", "My", "Mz"]
    limits = ["Central", "Lower", "Upper"]
    other_farm = NestedProperty.from_product(turbines, components, loads, limits)
    print(other_farm)

    # Loop over values, keys (the path to a leaf), or both
    print(">>> Loops")
    for leaf in farm.values():
        print(leaf)

    for key, leaf in farm.items():
        print(key, leaf)

    for key in farm.keys():
        print(key)

    for leaf in farm:
        print(leaf)

    # Check if a value is present in the values
    print(">>> is key in NestedDict?")
    first_key = list(farm.keys())[0]
    assert first_key in farm

    # Trees are printed as nested dictionaries
    print(">>> print")
    print(farm)

    # Number of values
    print(">>> length")
    print(len(farm))

    # Assign new value
    farm["T1", "blade", "Mx"] = 14
    # Create item if it doesn't exist
    farm["T100", "blade", "Mx"] = 14
    # Delete item
    del farm["T100", "blade", "Mx"]

    # Use tuples to access values
    assert farm["T2", "tower", "Mx"] == farm_data["T2"]["tower"]["Mx"]
    # This makes iterating through the data easier,
    # no nested for loops as in nested dictionaries,
    # no masks as in dataframes, ie farm[(farm[turbine] == "T1") & ...]
    my_func = lambda x: x
    for key, leaf in farm.items():
        farm[key] = my_func(leaf)

    # Extract data as a NestedDictionary
    turbine1 = farm.extract["T1"]
    turbine1_blade = farm.extract["T1", "blade"]
    all_blades = farm.extract["", "tower"]
    # Apply the same function to all values, as in dataframes
    farm.apply(lambda x: x + 1, inplace=True)

    # Logic operations
    print(">>> != and ==")
    print(farm != 1)
    print(farm == farm)

    # Deep copy
    farm2 = farm.copy()
    farm2["T1", "blade", "Mx"] = 10
    assert farm != farm2

    # Operations on all the values which return a single value
    print(">>> total, mean and std")
    print(farm.total())
    print(farm.mean())
    print(farm.std())

    # Arithmetics between trees that share the same keys
    print(">>> Arithmetics")
    print(farm + farm)
    print(-farm)
    print(farm - farm)
    print(farm + 1)
    print(farm - 1)

    print(farm)
    print(farm * 2)
    farm += 1
    print(farm / 10)

    print(">>> Methods inherited by MutableMapping")
    print(farm.popitem())
    farm["T100"] = 0
    print(farm.pop("T100"))
    print(farm.get("T100", "get default"))
    print(farm.setdefault("T100", {"blade": {"Mx": 1}}))
