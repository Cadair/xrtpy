"""Classes for describing channels on Hinode/XRT."""

__all__ = [
    "Geometry",
    "EntranceFilter",
    "Mirror",
    "Filter",
    "CCD",
    "Channel",
    "resolve_filter_name",
]

import sunpy.io.special
import sunpy.time

from astropy import units as u
from pathlib import Path

filename = Path(__file__).parent.absolute() / "data" / "xrt_channels_v0016.genx"

_channel_name_to_index_mapping = {
    "Open/Al_mesh": 0,
    "Al_poly/Open": 1,
    "C_poly/Open": 2,
    "Open/Ti_poly": 3,
    "Be_thin/Open": 4,
    "Be_med/Open": 5,
    "Al_med/Open": 6,
    "Open/Al_thick": 7,
    "Open/Be_thick": 8,
    "Al_poly/Al_mesh": 9,
    "Al_poly/Ti_poly": 10,
    "Al_poly/Al_thick": 11,
    "Al_poly/Be_thick": 12,
    "C_poly/Ti_poly": 13,
}


_genx_file = sunpy.io.special.genx.read_genx(filename)["SAVEGEN0"]


def resolve_filter_name(name):
    """
    Parses user provided filter name and converts it to a standard format used
    by XRTpy.

    Input filter name can be in standard XRT fits header format, e.g.
    Ti_poly or Open/Ti_poly, or in Sunpy standard, e.g. Open-Ti poly. The name
    may contain the names for both filter wheels or just one (but not "Open").
    If both filter wheel names are given they should be separated by either a
    dash (-) or a slash (/).  If there is dash or a slash in the name it
    should only be to separate the filter names. The filter wheel names may
    contain a space ( ) or an underscore (_).

    Returned value has two filter names separated by a slash (/) and each
    filter wheel name will contain only letters and (in most cases) an
    underscore (no spaces).
    """
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    # Note: not including Gband for now
    filters1 = ["Al_poly", "C_poly", "Be_thin", "Be_med", "Al_med"]
    filters2 = ["Al_mesh", "Ti_poly", "Al_thick", "Be_thick"]
    if "-" in name:
        fw1, fw2 = name.split("-")
        fw1 = fw1.capitalize().replace(" ", "_")
        if fw1 not in filters1 and fw1 != "Open":
            raise ValueError("Cannot interpret name of filter1")
        fw2 = fw2.capitalize().replace(" ", "_")
        if fw2 not in filters2 and fw2 != "Open":
            raise ValueError("Cannot interpret name of filter2")
        name = f"{fw1}/{fw2}"
    elif "/" in name:
        fw1, fw2 = name.split("/")
        fw1 = fw1.capitalize().replace(" ", "_")
        if fw1 not in filters1 and fw1 != "Open":
            raise ValueError("Cannot interpret name of filter1")
        fw2 = fw2.capitalize().replace(" ", "_")
        if fw2 not in filters2 and fw2 != "Open":
            raise ValueError("Cannot interpret name of filter2")
        name = f"{fw1}/{fw2}"
    else:
        # only one filter wheel name given
        name = name.capitalize().replace(" ", "_")
        if name in filters1:
            name = f"{name}/Open"
        elif name in filters2:
            name = f"Open/{name}"
        else:
            raise ValueError(f"Cannot interpret filter {name}")
    return name


class Geometry:
    """The physical geometric parameters of the X-Ray Telescope (XRT) on board the Hinode spacecraft."""

    _genx_file = _genx_file

    def __init__(self, index):
        self._channel_index = index
        self._geom_data = self._genx_file[self._channel_index]["GEOM"]

    @property
    def geometry_name(
        self,
    ) -> str:
        """Hinode/XRT flight model geometry."""
        return self._geom_data["LONG_NAME"]

    @property
    @u.quantity_input
    def geometry_focal_len(self) -> u.cm:
        """XRT flight model geometry focal length."""
        return u.Quantity(self._geom_data["FOC_LEN"], u.cm)

    @property
    @u.quantity_input
    def geometry_aperture_area(self) -> u.cm**2:
        """XRT flight model geometry aperture area."""
        return u.Quantity(self._geom_data["APERTURE_AREA"], u.cm**2)


class EntranceFilter:
    """
    Entrance filter properties.

    Thin prefilters cover the narrow annular entrance aperture of the XRT
    serving two main purposes:

    1. Reduce the visible light entering the instrument.
    2. Reduce the heat load in the instrument.
    """

    def __init__(self, index):
        self._channel_index = index
        self._en_filter_data = self._genx_file[self._channel_index]["EN_FILTER"]

    @property
    def entrancefilter_density(self) -> u.g * u.cm**-3:
        r"""XRT entrance filter material density in g/cm\ :sup:`3`\ ."""
        return u.Quantity(self._en_filter_data["DENS"], u.g * u.cm**-3)

    @property
    def entrancefilter_material(self) -> str:
        """XRT entrance filter material."""
        return self._en_filter_data["MATERIAL"]

    @property
    def entrancefilter_mesh_transmission(self):
        """Transmission of mesh filter substrate."""
        return self._en_filter_data["MESH_TRANS"]

    @property
    def entrancefilter_name(self) -> str:
        """Entrance filter name."""
        return self._en_filter_data["LONG_NAME"]

    @property
    def number_of_wavelengths(self):
        """Data number length."""
        return self._en_filter_data["LENGTH"]

    @property
    def entrancefilter_substrate(self) -> str:
        """XRT entrance filter substrate."""
        return self._en_filter_data["SUBSTRATE"]

    @property
    @u.quantity_input
    def entrancefilter_wavelength(self) -> u.angstrom:
        """Array of wavelengths for entrance filter transmission in angstroms."""
        return u.Quantity(self._en_filter_data["WAVE"], u.angstrom)[
            : self.number_of_wavelengths
        ]

    @property
    @u.quantity_input
    def entrancefilter_thickness(self) -> u.angstrom:
        """XRT entrance filter material thickness in angstroms."""
        return u.Quantity(self._en_filter_data["THICK"], u.angstrom)

    @property
    def entrancefilter_transmission(self):
        """Entrance filter transmission."""
        return self._en_filter_data["TRANS"][: self.number_of_wavelengths]


class Mirror:
    """
    Grazing incidence mirror properties.

    Grazing-incidence optics used for soft X-ray imaging generally require a minimum of two surfaces.
    Since XRT is a two-bounce telescope, there are two mirror reflectivities.
    """

    def __init__(self, index, mirror_number):
        self._channel_index = index
        self._mirror_data = self._genx_file[self._channel_index][
            f"MIRROR{mirror_number}"
        ]

    @property
    @u.quantity_input
    def mirror_density(self) -> u.g * u.cm**-3:
        """Mirror mass density."""
        return u.Quantity(self._mirror_data["DENS"], u.g * u.cm**-3)

    @property
    @u.quantity_input
    def mirror_graze_angle(self) -> u.deg:
        """Mirror graze angle in units of degrees."""
        return u.Quantity(self._mirror_data["GRAZE_ANGLE"], u.deg)

    @property
    def mirror_name(self) -> str:
        """Hinode/XRT flight model mirror."""
        return self._mirror_data["LONG_NAME"]

    @property
    def mirror_material(self) -> str:
        """XRT flight model mirror material."""
        return self._mirror_data["MATERIAL"]

    @property
    @u.quantity_input
    def mirror_reflection(self) -> u.angstrom:
        """Reflection of a mirror."""
        return u.Quantity(self._mirror_data["REFL"], u.angstrom)[
            : self.number_of_wavelengths
        ]

    @property
    @u.quantity_input
    def mirror_wavelength(self) -> u.angstrom:
        """Array of wavelengths for mirror reflectance."""
        return u.Quantity(self._mirror_data["WAVE"], u.angstrom)[
            : self.number_of_wavelengths
        ]

    @property
    def number_of_wavelengths(self):
        """Data number length."""
        return self._mirror_data["LENGTH"]


class Filter:
    """
    X-ray filters using two filter wheels.

    The corresponding categories are used for both filter 1 and filter 2.
    """

    def __init__(self, index, filter_number):
        self._channel_index = index
        self._fp_filter_data = self._genx_file[self._channel_index][
            f"FP_FILTER{filter_number}"
        ]

    @property
    @u.quantity_input
    def filter_density(self) -> u.g * u.cm**-3:
        """XRT filter density."""
        return u.Quantity(self._fp_filter_data["DENS"], u.g * u.cm**-3)

    @property
    def filter_material(self) -> str:
        """XRT filter material."""
        return self._fp_filter_data["MATERIAL"]

    @property
    def filter_mesh_transmission(self):
        """Mesh transmission for the focal plane filter."""
        return self._fp_filter_data["MESH_TRANS"]

    @property
    def filter_name(self) -> str:
        """XRT filter name."""
        return self._fp_filter_data["LONG_NAME"]

    @property
    def number_of_wavelengths(self):
        """Data number length."""
        return self._fp_filter_data["LENGTH"]

    @property
    def filter_substrate(self) -> str:
        """XRT filter substrate."""
        return self._fp_filter_data["SUBSTRATE"]

    @property
    @u.quantity_input
    def filter_thickness(self) -> u.angstrom:
        """Filter thickness."""
        return u.Quantity(self._fp_filter_data["THICK"], u.angstrom)

    @property
    def filter_transmission(self):
        """Filter transmission."""
        return self._fp_filter_data["TRANS"][: self.number_of_wavelengths]

    @property
    @u.quantity_input
    def filter_wavelength(self) -> u.angstrom:
        """XRT filter wavelength in angstroms."""
        return u.Quantity(self._fp_filter_data["WAVE"], u.angstrom)[
            : self.number_of_wavelengths
        ]


class CCD:
    """Charge-coupled device (CCD) on board X-Ray Telescope (XRT) on the Hinode spacecraft."""

    def __init__(self, index):
        self._channel_index = index
        self._ccd_data = self._genx_file[self._channel_index]["CCD"]

    @property
    @u.quantity_input
    def ccd_energy_per_electron(self) -> u.eV / u.electron:
        """The energy necessary to dislodge one electron."""
        return u.Quantity(self._ccd_data["EV_PER_EL"], u.eV / u.electron)

    @property
    @u.quantity_input
    def ccd_full_well(self) -> u.electron:
        """Number of electrons for a CCD full well."""
        return u.Quantity(self._ccd_data["FULL_WELL"], u.electron)

    @property
    @u.quantity_input
    def ccd_gain_left(self) -> u.electron / u.DN:
        """Gain when reading the left port of the CCD."""
        return u.Quantity(self._ccd_data["GAIN_L"], u.electron / u.DN)

    @property
    @u.quantity_input
    def ccd_gain_right(self) -> u.electron / u.DN:
        """Gain when reading the right port of the CCD."""
        return u.Quantity(57.5, u.electron / u.DN)

    @property
    def ccd_name(self) -> str:
        """Hinode/XRT flight model CCD."""
        return self._ccd_data["LONG_NAME"]

    @property
    def number_of_wavelengths(self):
        """Data number length."""
        return self._ccd_data["LENGTH"]

    @property
    @u.quantity_input
    def ccd_pixel_size(self) -> u.micron:
        """CCD pixel size in micrometers."""
        return u.Quantity(self._ccd_data["PIXEL_SIZE"], u.micron)

    @property
    def ccd_quantum_efficiency(self):
        """Quantum efficiency of the CCD."""
        return self._ccd_data["QE"][: self.number_of_wavelengths]

    @property
    @u.quantity_input
    def ccd_wavelength(self) -> u.angstrom:
        """Array of wavelengths for the CCD quantum efficiency in angstroms."""
        return u.Quantity(self._ccd_data["WAVE"], u.angstrom)[
            : self.number_of_wavelengths
        ]


class Channel:
    """
    XRTpy

    Available channels: ``"Al_mesh"``, ``"Al_poly"``,  ``"C_poly"``,
    ``"Ti_poly"``, ``"Be_thin"``, ``"Be_med"``, ``"Al_med"``, ``"Al_thick"``,
    ``"Be_thick"`` , ``"Al_poly/Al_mesh"``, ``"Al_poly/Ti_poly"``,
    ``"Al_poly/Al_thick"``, ``"Al_poly/Be_thick"`` , ``"C_poly/Ti_poly"``
    """

    def __init__(self, name):
        name = resolve_filter_name(name)
        if name in _channel_name_to_index_mapping:
            self._channel_index = _channel_name_to_index_mapping[name]
            self._channel_data = _genx_file[self._channel_index]
            self._geometry = Geometry(self._channel_index)
            self._entrancefilter = EntranceFilter(self._channel_index)
            self._mirror_1 = Mirror(self._channel_index, 1)
            self._mirror_2 = Mirror(self._channel_index, 2)
            self._filter_1 = Filter(self._channel_index, 1)
            self._filter_2 = Filter(self._channel_index, 2)
            self._ccd = CCD(self._channel_index)
        else:
            raise ValueError(
                f"{name} is not a valid channel. The available channels are:"
                f" {list(_channel_name_to_index_mapping.keys())}"
            )

    @property
    def geometry(self) -> Geometry:
        return self._geometry

    @property
    def entrancefilter(self) -> EntranceFilter:
        return self._entrancefilter

    @property
    def mirror_1(self) -> Mirror:
        return self._mirror_1

    @property
    def mirror_2(self) -> Mirror:
        return self._mirror_2

    @property
    def filter_1(self) -> Filter:
        return self._filter_1

    @property
    def filter_2(self) -> Filter:
        return self._filter_2

    @property
    def ccd(self) -> CCD:
        return self._ccd

    def __str__(self):
        """Readable printout."""
        return f"XRT Channel for {self.name}"

    def __repr__(self):
        """Code representation."""
        return f"Channel({repr(self.name)})"

    @property
    def name(self) -> str:
        """Name of XRT X-Ray channel."""
        name = self._channel_data["NAME"]
        name = name.replace("-", "_")
        name = resolve_filter_name(name)
        return name

    @property
    @u.quantity_input
    def wavelength(self) -> u.angstrom:
        """Array of wavelengths for every X-ray channel in angstroms."""
        return u.Quantity(self._channel_data["WAVE"], u.angstrom)[
            : self.number_of_wavelengths
        ]

    @property
    def transmission(self):
        """Get channel transmission."""
        return self._channel_data["TRANS"][: self.number_of_wavelengths]

    @property
    def number_of_wavelengths(self):
        """Data number length."""
        return self._channel_data["LENGTH"]

    @property
    def observatory(self) -> str:
        """The spacecraft name."""
        return self._channel_data["OBSERVATORY"]

    @property
    def instrument(self) -> str:
        """X-Ray Telescope -XRT."""
        return self._channel_data["INSTRUMENT"]
