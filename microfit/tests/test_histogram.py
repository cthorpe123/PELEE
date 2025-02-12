"""Unit Tests for plotting.histogram module"""
import unittest

from ..histogram import (
    Histogram,
    HistogramGenerator,
    Binning,
    RunHistGenerator,
    MultiChannelBinning,
    MultiChannelHistogram,
)
from ..parameters import Parameter, ParameterSet
import numpy as np
import pandas as pd
import uncertainties.unumpy as unumpy
import logging
from ..statistics import fronebius_nearest_psd


class TestHistogram(unittest.TestCase):
    def assertIsExactInstance(self, obj, cls):
        self.assertEqual(type(obj), cls, f"{obj} is not an exact instance of {cls}")

    def setUp(self):
        self.test_cases = [
            (Histogram, self.make_test_binning(multichannel=False, with_query=False)),
            (Histogram, self.make_test_binning(multichannel=False, with_query=True)),
            (
                MultiChannelHistogram,
                self.make_test_binning(multichannel=True, with_query=False),
            ),
            (
                MultiChannelHistogram,
                self.make_test_binning(multichannel=True, with_query=True),
            ),
            # Add more tuples as needed
        ]

    def make_test_binning(
        self, multichannel=False, with_query=False, second_query="matching"
    ):
        bin_edges = np.array([0, 1, 2, 3])
        first_channel_binning = Binning("x", bin_edges, "x-axis label")
        if with_query:
            first_channel_binning.selection_query = "bdt > 0.5"
        if not multichannel:
            return first_channel_binning

        second_channel_binning = Binning("y", bin_edges, "y-axis label")
        second_query_string = {
            "matching": "bdt > 0.5",
            "non_matching": "bdt < 0.5",
            "overlapping": "bdt < 0.8",
        }[second_query]
        if with_query:
            second_channel_binning.selection_query = second_query_string
        binning = MultiChannelBinning([first_channel_binning, second_channel_binning])
        return binning

    def make_test_bincounts(self, binning):
        """Make a test bincounts array for a given binning"""
        return np.arange(binning.n_bins) + 10

    def make_test_covariance_matrix(self, binning, diagonal=False):
        """Make a test covariance matrix for a given binning"""
        # The covariance matrix has to have shape (n_bins, n_bins)
        # and be positive semi-definite
        n_bins = binning.n_bins
        covariance_matrix = np.zeros((n_bins, n_bins))
        for i in range(n_bins):
            covariance_matrix[i, i] = (i + 1) * 0.01
        if diagonal:
            return covariance_matrix

        # add off-diagonal elements
        np.random.seed(0)
        covariance_matrix += np.random.rand(n_bins, n_bins) * 0.01
        return fronebius_nearest_psd(covariance_matrix)

    def test_copy(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                # make sure that the copy is deep
                bin_counts = self.make_test_bincounts(binning)
                covariance_matrix = self.make_test_covariance_matrix(binning)
                hist = HistogramClass(
                    binning,
                    bin_counts,
                    covariance_matrix=covariance_matrix,
                    label="hist",
                    tex_string="hist",
                )
                hist_copy = hist.copy()
                self.assertEqual(hist, hist_copy)
                self.assertIsNot(hist, hist_copy)
                # assert that the type is correct
                self.assertIsExactInstance(hist_copy, HistogramClass)

    def test_uncorrelated(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                bin_counts1 = self.make_test_bincounts(binning)
                bin_counts2 = bin_counts1 + 3
                covariance_matrix = self.make_test_covariance_matrix(
                    binning, diagonal=True
                )
                uncertainties1 = np.sqrt(np.diag(covariance_matrix))
                uncertainties2 = np.sqrt(np.diag(covariance_matrix))

                hist1 = HistogramClass(
                    binning,
                    bin_counts1,
                    uncertainties1,
                    label="hist1",
                    tex_string="hist1",
                )
                hist2 = HistogramClass(
                    binning,
                    bin_counts2,
                    uncertainties2,
                    label="hist2",
                    tex_string="hist2",
                )

                hist_sum = hist1 + hist2
                hist_diff = hist1 - hist2

                self.assertIsExactInstance(hist_sum, HistogramClass)
                self.assertIsExactInstance(hist_diff, HistogramClass)
                expected_uncertainties = np.sqrt(
                    uncertainties1 ** 2 + uncertainties2 ** 2
                )

                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_sum.bin_counts),
                    bin_counts1 + bin_counts2,
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_sum.bin_counts), expected_uncertainties
                )
                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_diff.bin_counts),
                    bin_counts1 - bin_counts2,
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_diff.bin_counts), expected_uncertainties
                )

    def test_correlated(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                bin_counts1 = self.make_test_bincounts(binning)
                bin_counts2 = bin_counts1 + 3
                covariance_matrix = self.make_test_covariance_matrix(
                    binning, diagonal=False
                )
                uncertainties1 = np.sqrt(np.diag(covariance_matrix))
                uncertainties2 = np.sqrt(np.diag(covariance_matrix))

                hist1 = HistogramClass(
                    binning,
                    bin_counts1,
                    covariance_matrix=covariance_matrix,
                    label="hist1",
                    tex_string="hist1",
                )
                hist2 = HistogramClass(
                    binning,
                    bin_counts2,
                    covariance_matrix=covariance_matrix,
                    label="hist2",
                    tex_string="hist2",
                )

                hist_sum = hist1 + hist2
                hist_diff = hist1 - hist2

                self.assertIsExactInstance(hist_sum, HistogramClass)
                self.assertIsExactInstance(hist_diff, HistogramClass)
                expected_uncertainties = np.sqrt(
                    uncertainties1 ** 2 + uncertainties2 ** 2
                )

                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_sum.bin_counts),
                    bin_counts1 + bin_counts2,
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_sum.bin_counts), expected_uncertainties
                )
                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_diff.bin_counts),
                    bin_counts1 - bin_counts2,
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_diff.bin_counts), expected_uncertainties
                )

    def test_fluctuation(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                bin_counts = self.make_test_bincounts(binning)
                covariance_matrix = self.make_test_covariance_matrix(binning)
                hist = HistogramClass(
                    binning,
                    bin_counts,
                    covariance_matrix=covariance_matrix,
                    label="hist",
                    tex_string="hist",
                )
                # fluctuate the histogram and check that the fluctuated bin counts are distributed according to the covariance matrix
                fluctuated_counts = []
                for i in range(10000):
                    fluctuated_hist = hist.fluctuate(seed=i)
                    self.assertIsExactInstance(fluctuated_hist, HistogramClass)
                    fluctuated_counts.append(fluctuated_hist.nominal_values)
                fluctuated_counts = np.array(fluctuated_counts)

                # calculate covariance matrix of fluctuated counts with numpy
                covariance_matrix_fluct = np.cov(fluctuated_counts, rowvar=False)

                # this should be close to the expectation value
                np.testing.assert_array_almost_equal(
                    covariance_matrix, covariance_matrix_fluct, decimal=2
                )

    def test_division(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                bin_counts1 = self.make_test_bincounts(binning)
                bin_counts2 = bin_counts1 + 3
                covariance_matrix1 = self.make_test_covariance_matrix(binning)
                covariance_matrix2 = self.make_test_covariance_matrix(binning)
                uncertainties1 = np.sqrt(np.diag(covariance_matrix1))
                uncertainties2 = np.sqrt(np.diag(covariance_matrix2))

                hist1 = HistogramClass(
                    binning,
                    bin_counts1,
                    covariance_matrix=covariance_matrix1,
                    label="hist1",
                    tex_string="hist1",
                )
                hist2 = HistogramClass(
                    binning,
                    bin_counts2,
                    covariance_matrix=covariance_matrix2,
                    label="hist2",
                    tex_string="hist2",
                )

                hist_div = hist1 / hist2
                self.assertIsExactInstance(hist_div, HistogramClass)

                expected_uncertainties = np.sqrt(
                    (uncertainties1 / bin_counts2) ** 2
                    + (uncertainties2 * bin_counts1 / bin_counts2 ** 2) ** 2
                )

                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_div.bin_counts),
                    bin_counts1 / bin_counts2,
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_div.bin_counts), expected_uncertainties
                )
                fluctuated_divisions = []
                # To test error propagation, we fluctuate hist1 and hist2 and divide them. The covariance matrix
                # of the fluctuated divisions should be close to the expected covariance matrix that we get
                # from the division function.
                for i in range(10000):
                    fluctuated_hist1 = hist1.fluctuate(seed=i)
                    # It's important not to repeat seeds here, otherwise the values will be correlated
                    # when they should not be.
                    fluctuated_hist2 = hist2.fluctuate(seed=i + 10000)
                    self.assertIsExactInstance(fluctuated_hist1, HistogramClass)
                    self.assertIsExactInstance(fluctuated_hist2, HistogramClass)
                    fluctuated_division = fluctuated_hist1 / fluctuated_hist2
                    self.assertIsExactInstance(fluctuated_division, HistogramClass)
                    fluctuated_divisions.append(fluctuated_division.nominal_values)
                fluctuated_divisions = np.array(fluctuated_divisions)

                # calculate covariance matrix of fluctuated divisions with numpy
                covariance_matrix = np.cov(fluctuated_divisions, rowvar=False)

                # get expectation histogram
                expected_div_hist = hist1 / hist2
                # check nominal values
                np.testing.assert_array_almost_equal(
                    fluctuated_divisions.mean(axis=0),
                    expected_div_hist.nominal_values,
                    decimal=3,
                )
                # check covariance matrix
                np.testing.assert_array_almost_equal(
                    covariance_matrix, expected_div_hist.covariance_matrix, decimal=4
                )

    def test_scalar_multiplication(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                bin_counts = self.make_test_bincounts(binning)
                covariance_matrix = self.make_test_covariance_matrix(binning)
                hist = HistogramClass(
                    binning,
                    bin_counts,
                    covariance_matrix=covariance_matrix,
                    label="hist",
                    tex_string="hist",
                )
                # multiply by a scalar
                hist_mult = hist * 2
                expected_uncertainties = np.sqrt(np.diag(covariance_matrix)) * 2
                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_mult.bin_counts), bin_counts * 2
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_mult.bin_counts), expected_uncertainties
                )
                # multiply from the left
                hist_mult = 2 * hist
                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_mult.bin_counts), bin_counts * 2
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_mult.bin_counts), expected_uncertainties
                )

    # Test conversion to and from dict
    def test_dict_conversion(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                bin_counts = self.make_test_bincounts(binning)
                covariance_matrix = self.make_test_covariance_matrix(binning)
                hist = HistogramClass(
                    binning,
                    bin_counts,
                    covariance_matrix=covariance_matrix,
                    label="hist",
                    tex_string="hist",
                )
                hist_dict = hist.to_dict()
                hist_from_dict = HistogramClass.from_dict(hist_dict)
                self.assertEqual(hist, hist_from_dict)
                self.assertIsExactInstance(hist_from_dict, HistogramClass)

    def test_multiplication(self):
        for HistogramClass, binning in self.test_cases:
            with self.subTest(HistogramClass=HistogramClass, binning=binning):
                bin_counts1 = self.make_test_bincounts(binning)
                bin_counts2 = bin_counts1 + 3
                covariance_matrix1 = self.make_test_covariance_matrix(binning) * 0.1
                covariance_matrix2 = self.make_test_covariance_matrix(binning) * 0.2
                uncertainties1 = np.sqrt(np.diag(covariance_matrix1))
                uncertainties2 = np.sqrt(np.diag(covariance_matrix2))

                hist1 = HistogramClass(
                    binning,
                    bin_counts1,
                    covariance_matrix=covariance_matrix1,
                    label="hist1",
                    tex_string="hist1",
                )
                hist2 = HistogramClass(
                    binning,
                    bin_counts2,
                    covariance_matrix=covariance_matrix2,
                    label="hist2",
                    tex_string="hist2",
                )

                hist_mult = hist1 * hist2
                self.assertIsExactInstance(hist_mult, HistogramClass)

                expected_uncertainties = np.sqrt(
                    (uncertainties1 * bin_counts2) ** 2
                    + (uncertainties2 * bin_counts1) ** 2
                )

                np.testing.assert_array_almost_equal(
                    unumpy.nominal_values(hist_mult.bin_counts),
                    bin_counts1 * bin_counts2,
                )
                np.testing.assert_array_almost_equal(
                    unumpy.std_devs(hist_mult.bin_counts), expected_uncertainties
                )
                fluctuated_multiplications = []
                # To test error propagation, we fluctuate hist1 and hist2 and multiply them. The covariance matrix
                # of the fluctuated multiplications should be close to the expected covariance matrix that we get
                # from the multiplication function.
                for i in range(10000):
                    fluctuated_hist1 = hist1.fluctuate(seed=i)
                    # It's important not to repeat seeds here, otherwise the values will be correlated
                    # when they should not be.
                    fluctuated_hist2 = hist2.fluctuate(seed=i + 10000)
                    self.assertIsExactInstance(fluctuated_hist1, HistogramClass)
                    self.assertIsExactInstance(fluctuated_hist2, HistogramClass)
                    fluctuated_multiplication = fluctuated_hist1 * fluctuated_hist2
                    self.assertIsExactInstance(
                        fluctuated_multiplication, HistogramClass
                    )
                    fluctuated_multiplications.append(
                        fluctuated_multiplication.nominal_values
                    )
                fluctuated_multiplications = np.array(fluctuated_multiplications)

                # calculate covariance matrix of fluctuated multiplications with numpy
                covariance_matrix = np.cov(fluctuated_multiplications, rowvar=False)

                # get expectation histogram
                expected_mult_hist = hist1 * hist2
                # check nominal values
                np.testing.assert_array_almost_equal(
                    fluctuated_multiplications.mean(axis=0),
                    expected_mult_hist.nominal_values,
                    decimal=1,
                )
                # check covariance matrix
                np.testing.assert_array_almost_equal(
                    covariance_matrix, expected_mult_hist.covariance_matrix, decimal=1
                )


class TestHistogramGenerator(unittest.TestCase):
    """Test the HistogramGenerator class.
    
    Functionality is tested for single-channel and multi-channel binning.
    """

    def assertIsExactInstance(self, obj, cls):
        self.assertEqual(type(obj), cls, f"{obj} is not an exact instance of {cls}")

    def setUp(self):
        self.test_cases = [
            {"multichannel": False, "with_query": False},
            {"multichannel": False, "with_query": True},
            {"multichannel": True, "with_query": False},
            {"multichannel": True, "with_query": True},
        ]

    def make_dataframe(self):
        df = pd.DataFrame()
        np.random.seed(0)
        df["energy"] = np.random.lognormal(0, 0.5, 1000)
        df["angle"] = np.random.uniform(0, 3.14, 1000)
        df["bdt"] = np.random.uniform(0, 1, 1000)
        df["weights"] = np.random.uniform(0, 1, 1000)
        # To test multisim weights, create a column with a list of weights for each event. They
        # should be close to one and have a length of 100.
        df["multisim_weights"] = [
            1000 * np.random.normal(loc=1, size=100, scale=0.1) for _ in range(len(df))
        ]
        return df

    def make_test_binning(
        self, multichannel=False, with_query=False, second_query="matching"
    ):
        first_channel_binning = Binning.from_config("energy", 10, (0, 100), "Energy")
        if with_query:
            first_channel_binning.selection_query = "bdt > 0.5"
        if not multichannel:
            return first_channel_binning

        second_channel_binning = Binning.from_config("angle", 10, (0, 3.14), "Angle")
        second_query_string = {
            "matching": "bdt > 0.5",
            "non_matching": "bdt < 0.5",
            "overlapping": "bdt < 0.8",
        }[second_query]
        if with_query:
            second_channel_binning.selection_query = second_query_string
        binning = MultiChannelBinning([first_channel_binning, second_channel_binning])
        return binning

    def test_generate(self):
        df = self.make_dataframe()
        for test_case in self.test_cases:
            with self.subTest(test_case=test_case):
                binning = self.make_test_binning(**test_case)
                generator = HistogramGenerator(df, binning)
                histogram = generator.generate()
                if test_case["multichannel"]:
                    self.assertIsExactInstance(histogram, MultiChannelHistogram)
                self.assertEqual(histogram.binning, binning)
                self.assertEqual(len(histogram.bin_counts), binning.n_bins)
                self.assertEqual(len(histogram.std_devs), binning.n_bins)

    def test_subchannel_extraction(self):

        df = self.make_dataframe()
        for second_query in ["matching", "non_matching", "overlapping"]:
            mc_binning = self.make_test_binning(
                multichannel=True, with_query=True, second_query=second_query
            )
            generator = HistogramGenerator(df, mc_binning)
            mc_histogram = generator.generate()
            self.assertIsExactInstance(mc_histogram, MultiChannelHistogram)

            for binning in mc_binning:
                channel_generator = HistogramGenerator(df, binning)
                channel_histogram = channel_generator.generate()
                self.assertIsExactInstance(channel_histogram, Histogram)
                self.assertEqual(channel_histogram, mc_histogram[binning.label])

    def test_subclass_with_parameters(self):
        # create example DataFrame with additional columns 'x' and 'y'
        df = self.make_dataframe()
        for test_case in self.test_cases:
            with self.subTest(test_case=test_case):
                binning = self.make_test_binning(**test_case)
                # Create a subclass of the HistogramGenerator that overrides the
                # adjust_weights method. We want to simulate a parameter that is the spectral
                # index, so events should be re-weighted according to $E^{-\Delta\gamma}$,
                # where $\Delta\gamma$ is the (variation of the) spectral index.

                class SpectralIndexGenerator(HistogramGenerator):
                    def adjust_weights(self, dataframe, base_weights):
                        delta_gamma = self.parameters["delta_gamma"].m
                        return base_weights * dataframe["energy"] ** delta_gamma

                # Create a ParameterSet with a single parameter
                parameters = ParameterSet(
                    [Parameter("delta_gamma", 0.5, bounds=(-1, 1))]
                )
                # Initialize the HistogramGenerator
                generator = SpectralIndexGenerator(df, binning, parameters=parameters)
                # To cross-check, we create a dataframe where we already apply the re-weighting
                # and create a histogram from that
                df_reweighted = df.copy()
                df_reweighted["weights"] = (
                    df_reweighted["weights"] * df_reweighted["energy"] ** 0.5
                )
                generator_reweighted = HistogramGenerator(df_reweighted, binning)
                # Generate the histogram
                histogram = generator.generate()
                crosscheck_histogram = generator_reweighted.generate()
                self.assertEqual(histogram, crosscheck_histogram)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(histogram, MultiChannelHistogram)

    def test_caching(self):
        df = self.make_dataframe()
        for test_case in self.test_cases:
            with self.subTest(test_case=test_case):
                binning = self.make_test_binning(**test_case)
                # Create a subclass of the HistogramGenerator that overrides the
                # adjust_weights method. We want to simulate a parameter that is the spectral
                # index, so events should be re-weighted according to $E^{-\Delta\gamma}$,
                # where $\Delta\gamma$ is the (variation of the) spectral index.

                class SpectralIndexGenerator(HistogramGenerator):
                    def adjust_weights(self, dataframe, base_weights):
                        delta_gamma = self.parameters["delta_gamma"].m
                        return base_weights * dataframe["energy"] ** delta_gamma

                # Create a ParameterSet with a single parameter
                parameters = ParameterSet(
                    [Parameter("delta_gamma", 0.5, bounds=(-1, 1))]
                )
                # Initialize the HistogramGenerator
                generator_cached = SpectralIndexGenerator(
                    df, binning, parameters=parameters, enable_cache=True
                )
                # To cross-check, we create a histogram generator without caching. The output
                # should always be the same.
                generator_uncached = SpectralIndexGenerator(
                    df, binning, parameters=parameters, enable_cache=False
                )
                hist_cached = generator_cached.generate()
                hist_uncached = generator_uncached.generate()
                self.assertEqual(hist_cached, hist_uncached)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(hist_cached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_uncached, MultiChannelHistogram)
                # add a query
                query = "bdt > 0.5"
                hist_cached = generator_cached.generate(extra_query=query)
                hist_uncached = generator_uncached.generate(extra_query=query)
                self.assertEqual(hist_cached, hist_uncached)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(hist_cached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_uncached, MultiChannelHistogram)
                # and remove again
                hist_cached = generator_cached.generate()
                hist_uncached = generator_uncached.generate()
                self.assertEqual(hist_cached, hist_uncached)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(hist_cached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_uncached, MultiChannelHistogram)
                # change parameter. Note that the parameter is automatically shared between the two generators,
                # so we only need to change it once.
                parameters["delta_gamma"].value = 0.0
                hist_cached = generator_cached.generate()
                hist_uncached = generator_uncached.generate()
                self.assertEqual(hist_cached, hist_uncached)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(hist_cached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_uncached, MultiChannelHistogram)
                # add a query
                hist_cached = generator_cached.generate(extra_query=query)
                hist_uncached = generator_uncached.generate(extra_query=query)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(hist_cached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_uncached, MultiChannelHistogram)
                # just to be sure, make a new HistogramGenerator without parameters
                # When delta_gamma == 0, the re-weighting should not change anything
                default_generator = HistogramGenerator(df, binning, enable_cache=False)
                hist_default = default_generator.generate(extra_query=query)
                self.assertEqual(hist_cached, hist_uncached)
                self.assertEqual(hist_cached, hist_default)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(hist_cached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_uncached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_default, MultiChannelHistogram)
                # and remove again
                hist_cached = generator_cached.generate()
                hist_uncached = generator_uncached.generate()
                self.assertEqual(hist_cached, hist_uncached)
                if test_case["multichannel"]:
                    self.assertIsExactInstance(hist_cached, MultiChannelHistogram)
                    self.assertIsExactInstance(hist_uncached, MultiChannelHistogram)


class TestRunHistGenerator(unittest.TestCase):
    def make_dataframe(self, n_samples=1000, data_like=False, with_multisim=False):
        df = pd.DataFrame()
        np.random.seed(0)
        # sampling energy from a slightly more realistic distribution
        df["energy"] = np.random.lognormal(0, 0.5, n_samples)
        df["angle"] = np.random.uniform(0, 3.14, n_samples)
        df["bdt"] = np.random.uniform(0, 1, n_samples)
        if data_like:
            df["weights"] = np.ones(n_samples)
            # data never contains multisim weights
            return df
        else:
            df["weights"] = np.random.uniform(0, 1, n_samples)
        if not with_multisim:
            return df
        # The 'weights_no_tune' column is used to calculate multisim uncertainties for GENIE
        # variables. For testing purposes, we just set it to the same as 'weights'.
        df["weights_no_tune"] = df["weights"]
        n_universes = 100
        for ms_column in ["weightsGenie", "weightsFlux", "weightsReint"]:
            df[ms_column] = [
                n_samples * np.random.normal(loc=1, size=n_universes, scale=0.1)
                for _ in range(len(df))
            ]
        # Also add unisim "knob" weights
        knob_v = [
            "knobRPA",
            "knobCCMEC",
            "knobAxFFCCQE",
            "knobVecFFCCQE",
            "knobDecayAngMEC",
            "knobThetaDelta2Npi",
        ]
        for knob in knob_v:
            df[f"{knob}up"] = 1.1
            df[f"{knob}dn"] = 0.9
        return df

    def test_get_data_hist(self):
        # Create some mock data
        rundata_dict = {
            "data": pd.DataFrame({"x": [1, 2, 3], "weights": [1, 1, 1]}),
            "mc": pd.DataFrame({"x": [1, 2, 3], "weights": [1, 1, 1]}),
            "ext": pd.DataFrame({"x": [1, 2, 3], "weights": [1, 1, 1]}),
        }
        binning = Binning("x", [0, 1, 2, 3, 4], "x")
        generator = RunHistGenerator(rundata_dict, binning, data_pot=1.0)

        # Test getting the data histogram
        data_hist = generator.get_data_hist()
        np.testing.assert_array_equal(data_hist.nominal_values, [0, 1, 1, 1])

        # Test getting the EXT histogram
        ext_hist = generator.get_data_hist(type="ext")
        np.testing.assert_array_equal(ext_hist.nominal_values, [0, 1, 1, 1])

        # Test scaling the EXT histogram
        ext_hist_scaled = generator.get_data_hist(type="ext", scale_to_pot=2)
        np.testing.assert_array_equal(ext_hist_scaled.nominal_values, [0, 2, 2, 2])


if __name__ == "__main__":
    unittest.main(argv=[""], verbosity=2, exit=False)
