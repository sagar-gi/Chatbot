import logging

from rasa_dm.util import all_subclasses

logger = logging.getLogger(__name__)


class Slot(object):
    type_name = None

    def __init__(self, name, initial_value=None, value_reset_delay=None):
        self.name = name
        self.value = initial_value
        self.initial_value = initial_value
        self._value_reset_delay = value_reset_delay

    def feature_dimensionality(self):
        """How many features this single slot creates.

        The dimensionality of the array returned by `as_feature` needs to correspond to this value."""
        return 1

    def value_reset_delay(self):
        """Returns after how many turns the value of the slot should be reset to the initial_value.

        If the delay is set to `None`, the slot will keep its value forever."""
        # TODO: this needs to be implemented - slots are not reset yet
        return self._value_reset_delay

    def as_feature(self):
        raise NotImplementedError("Each slot type needs to specify how its value can be converted to a feature.")

    def reset(self):
        self.value = self.initial_value

    def __str__(self):
        return "{}({}: {})".format(self.__class__.__name__, self.name, self.value)

    def __repr__(self):
        return "<{}({}: {})>".format(self.__class__.__name__, self.name, self.value)

    @staticmethod
    def resolve_by_type(type_name):
        """Returns a slots class by its type name."""

        for cls in all_subclasses(Slot):
            if cls.type_name == type_name:
                return cls
        raise ValueError("Unknown slot type name '{}'.".format(type_name))

    def additional_persistence_info(self):
        return {}


class FloatSlot(Slot):
    type_name = "float"

    def __init__(self, name, initial_value=None, value_reset_delay=None, max_value=1.0, min_value=0.0):
        super(FloatSlot, self).__init__(name, initial_value, value_reset_delay)
        self.max_value = max_value
        self.min_value = min_value

    def as_feature(self):
        try:
            capped_value = max(self.min_value, min(self.max_value, float(self.value)))
            covered_range = self.max_value - self.min_value if self.max_value - self.min_value > 0 else 1
            return [(capped_value - self.min_value) / covered_range]
        except (TypeError, ValueError):
            return [0.0]


class BooleanSlot(Slot):
    type_name = "bool"

    def as_feature(self):
        try:
            return [float(float(self.value) != 0.0) if self.value is not None else 0.0]
        except (TypeError, ValueError):
            # we couldn't convert the value to float - using default value
            return [0.0]


class TextSlot(Slot):
    type_name = "text"

    def as_feature(self):
        return [1.0 if self.value is not None else 0.0]


class ListSlot(Slot):
    type_name = "list"

    def as_feature(self):
        try:
            return [1.0 if self.value is not None and len(self.value) > 0 else 0.0]
        except (TypeError, ValueError):
            # we couldn't convert the value to a list - using default value
            return [0.0]


class UnfeaturizedSlot(Slot):
    type_name = "unfeaturized"

    def as_feature(self):
        return []

    def feature_dimensionality(self):
        return 0


class CategoricalSlot(Slot):
    type_name = "categorical"

    def __init__(self, name, values=None, initial_value=None, value_reset_delay=None):
        super(CategoricalSlot, self).__init__(name, initial_value, value_reset_delay)
        self.values = [str(v).lower() for v in values] if values else []

    def additional_persistence_info(self):
        return {"values": self.values}

    def as_feature(self):
        r = [0.0] * self.feature_dimensionality()

        try:
            for i, v in enumerate(self.values):
                if v == str(self.value).lower():
                    r[i] = 1.0
        except (TypeError, ValueError):
            # probably hit something strange
            return r
        return r

    def feature_dimensionality(self):
        return len(self.values)


class DataSlot(Slot):
    def __init__(self, name, initial_value=None, value_reset_delay=1):
        super(DataSlot, self).__init__(name, initial_value, value_reset_delay)

    def as_feature(self):
        raise NotImplementedError("Each slot type needs to specify how its value can be converted to a feature.")
