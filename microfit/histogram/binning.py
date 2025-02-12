from dataclasses import dataclass, fields
from typing import List, Optional, Tuple, Union
from microfit.selections import find_common_selection

import numpy as np

@dataclass
class Binning:
    """Binning for a variable

    Attributes:
    -----------
    variable : str
        Name of the variable being binned
    bin_edges : np.ndarray
        Array of bin edges
    label : str
        Label of the binning. In a multi-dimensional binning, this should be 
        a unique key.
    variable_tex : str, optional
        LaTeX representation of the variable (default is None) that can be used
        in plots.
    is_log : bool, optional
        Whether the binning is logarithmic or not (default is False)
    selection_query : str, optional
        Query to be applied to the dataframe before generating the histogram.
    """

    variable: str
    bin_edges: np.ndarray
    label: Optional[str] = None
    variable_tex: Optional[str] = None
    is_log: bool = False
    selection_query: Optional[str] = None

    def __eq__(self, other):
        for field in fields(self):
            attr_self = getattr(self, field.name)
            attr_other = getattr(other, field.name)
            if field.name == "label":
                # There may be situations where a label is undefined (for instance, when
                # loading detector systematics). In this case, we don't want to compare
                # the labels.
                if attr_self is None or attr_other is None:
                    continue
            if isinstance(attr_self, np.ndarray) and isinstance(attr_other, np.ndarray):
                if not np.array_equal(attr_self, attr_other):
                    return False
            else:
                if attr_self != attr_other:
                    return False
        return True

    def __post_init__(self):
        if isinstance(self.bin_edges, list):
            self.bin_edges = np.array(self.bin_edges)
        if self.variable_tex is None:
            self.variable_tex = self.variable
        assert self.variable_tex is not None

    def __len__(self):
        return self.n_bins

    @classmethod
    def from_config(
        cls,
        variable: str,
        n_bins: int,
        limits: Tuple[float, float],
        variable_tex: Optional[str] = None,
        is_log: bool = False,
        label: Optional[str] = None,
    ):
        """Create a Binning object from a typical binning configuration

        Parameters:
        -----------
        variable : str
            Name of the variable being binned
        n_bins : int
            Real of bins
        limits : tuple
            Tuple of lower and upper limits
        variable_tex : str, optional
            Label for the binned variable. This will be used to label the x-axis in plots.
        is_log : bool, optional
            Whether the binning is logarithmic or not (default is False)
        label : str, optional
            Label of the binning. In a multi-dimensional binning, this should be
            a unique key.

        Returns:
        --------
        Binning
            A Binning object with the specified bounds
        """
        if is_log:
            bin_edges = np.geomspace(*limits, n_bins + 1)
        else:
            bin_edges = np.linspace(*limits, n_bins + 1)
        label = variable if label is None else label
        return cls(variable, bin_edges, label, variable_tex, is_log=is_log)

    @property
    def n_bins(self):
        """Real of bins"""
        return len(self.bin_edges) - 1

    @property
    def bin_centers(self):
        """Array of bin centers"""
        if self.is_log:
            return np.sqrt(self.bin_edges[1:] * self.bin_edges[:-1])
        else:
            return (self.bin_edges[1:] + self.bin_edges[:-1]) / 2

    def to_dict(self):
        """Return a dictionary representation of the binning."""
        return self.__dict__

    @classmethod
    def from_dict(cls, state):
        """Create a Binning object from a dictionary representation of the binning."""
        return cls(**state)

    def copy(self):
        """Create a copy of the binning."""
        return Binning(**self.to_dict())
    

@dataclass
class MultiChannelBinning:
    """Binning for multiple channels.

    This can be used to define multi-channel binnings of the same data as well as
    binnings for different selections. For every channel, we may have a different
    Binning that may have its own selection query. Using this binning definition,
    the HistogramGenerator can make multi-channel histograms that may include
    correlations between bins and channels.

    Note that this is different from a multi-dimensional binning. The binnings
    defined in this class are still 1-dimensional, but the HistogramGenerator
    can create an unrolled 1-dimensional histogram from all the channels that
    includes correlations between bins of different channels.
    """

    binnings: List[Binning]
    is_log: bool = False

    def __post_init__(self):
        self.ensure_unique_labels()

    def ensure_unique_labels(self):
        """Ensure that the `label` properties of the binnings in a MultiChannelBinning are unique."""
        used_labels = set()
        counter = 0
        for binning in self.binnings:
            if binning.label in used_labels:
                binning.label = f"{binning.label}_{counter}"
                counter += 1
            used_labels.add(binning.label)

    def reduce_selection(self):
        """Extract the common selection query from all channels and reduce the
        selection queries of all channels to only include the unique selections.

        Returns
        -------
        str
            A single selection query that can be applied to the dataframe before
            making the histogram.
        """
        selection_queries = [b.selection_query for b in self.binnings]
        common_selection, unique_selections = find_common_selection(selection_queries)
        for binning, unique_selection in zip(self.binnings, unique_selections):
            binning.selection_query = unique_selection
        return common_selection

    @property
    def label(self) -> str:
        """Label of the unrolled binning."""
        return "Global Bin Real"

    @property
    def labels(self) -> List[Union[str, None]]:
        """Labels of all channels."""
        return [b.label for b in self.binnings]

    @property
    def n_channels(self):
        """Real of channels."""
        return len(self.binnings)

    @property
    def n_bins(self):
        """Real of bins in all channels."""
        return sum([len(b) for b in self.binnings])

    @property
    def consecutive_bin_edges(self) -> List[np.ndarray]:
        """Get the bin edges of all channels.

        The bin edges of all channels are concatenated
        into a single array, which can be passed to np.histogramdd as follows:
        >>> bin_edges = consecutive_bin_edges
        >>> hist, _ = np.histogramdd(data, bins=bin_edges)

        Returns
        -------
        List[np.ndarray]
            List of arrays of bin edges of all channels.
        """
        return [b.bin_edges for b in self.binnings]

    @property
    def variables(self) -> List[str]:
        """Get the variables of all channels.

        Returns
        -------
        List[str]
            List of variables of all channels.
        """
        return [b.variable for b in self.binnings]

    @property
    def selection_queries(self) -> List[Union[str, None]]:
        """Get the selection queries of all channels.

        Returns
        -------
        List[str]
            List of selection queries of all channels.
        """
        return [b.selection_query for b in self.binnings]

    def get_unrolled_binning(self) -> Binning:
        """Get an unrolled binning of all channels.

        The bins will just be labeled as 'Global bin number' and the
        variable will be 'none'. An unrolled binning cannot be used to
        create a histogram directly, but it can be used for plotting.
        """
        bin_edges = np.arange(self.n_bins + 1)
        return Binning("none", bin_edges, label="unrolled", variable_tex="Global bin number")

    def _idx_channel(self, key: Union[int, str]) -> int:
        """Get the index of a channel from the key.
        The key may be a numeric index or a string label.

        Parameters
        ----------
        key : int or str
            Index or label of the channel.
        """
        if isinstance(key, int):
            return key
        elif isinstance(key, str):
            return self.labels.index(key)
        else:
            raise ValueError(f"Invalid key {key}. Must be an integer or a string.")

    def _channel_bin_idx(self, key: Union[int, str]) -> List[int]:
        """Get the indices of bins in the unrolled binning belonging to a channel.

        The bin counts from the channel can be extracted from the full bin counts
        using these indices as follows:
        >>> idx = _channel_bin_idx(key)
        >>> channel_bin_counts = bin_counts[idx]

        Parameters
        ----------
        key : int or str
            Index or label of the channel.
        bin_idx : int
            Index of the bin in the channel.

        Returns
        -------
        List[int]
            List of indices of bins belonging to the channel.
        """
        idx = self._idx_channel(key)
        binning = self.binnings[idx]
        start_idx = sum([len(b) for b in self.binnings[:idx]])
        return list(range(start_idx, start_idx + len(binning)))

    def __getitem__(self, key: Union[int, str]) -> Binning:
        """Get the binning of a given channel.

        Parameters
        ----------
        key : int or str
            Index or label of the channel.

        Returns
        -------
        Binning
            Binning of the channel.
        """
        return self.binnings[self._idx_channel(key)]

    def __iter__(self):
        for binning in self.binnings:
            yield binning

    def __len__(self):
        return self.n_channels
    
    def copy(self):
        """Create a copy of the binning."""
        return MultiChannelBinning([b.copy() for b in self.binnings], self.is_log)