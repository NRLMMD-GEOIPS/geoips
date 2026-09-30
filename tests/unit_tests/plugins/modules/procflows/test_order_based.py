# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for the class-based OrderBased procflow."""

from geoips.plugins.modules.procflows.order_based import OrderBased


class TestOrderBased:
    """Tests for the OrderBased procflow class."""

    def test_class_has_correct_attrs(self):
        """Expected class-level interface, family, name, and data_tree attrs."""
        ob = OrderBased()
        assert ob.interface == "procflows"
        assert ob.family == "order_based"
        assert ob.name == "order_based"
        assert ob.data_tree is True
