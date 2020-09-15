import logging

from xia2.Driver.DriverFactory import DriverFactory

logger = logging.getLogger("xia2.Wrappers.Dials.ExportMtz")


def ExportMtz(DriverType=None):
    """A factory for ExportMtzWrapper classes."""

    DriverInstance = DriverFactory.Driver(DriverType)

    class ExportMtzWrapper(DriverInstance.__class__):
        def __init__(self):
            DriverInstance.__class__.__init__(self)
            self.set_executable("dials.export")

            self.crystal_name = None
            self.project_name = None
            self._experiments_filename = None
            self._reflections_filename = None
            self._mtz_filename = "hklout.mtz"
            self._partiality_threshold = 0.99
            self._combine_partials = True
            self._intensity_choice = "profile+sum"

        def set_intensity_choice(self, choice):
            self._intensity_choice = choice

        def set_partiality_threshold(self, partiality_threshold):
            self._partiality_threshold = partiality_threshold

        def set_combine_partials(self, combine_partials):
            self._combine_partials = combine_partials

        def set_experiments_filename(self, experiments_filename):
            self._experiments_filename = experiments_filename

        def get_experiments_filename(self):
            return self._experiments_filename

        def set_reflections_filename(self, reflections_filename):
            self._reflections_filename = reflections_filename

        def get_reflections_filename(self):
            return self._reflections_filename

        def set_mtz_filename(self, mtz_filename):
            self._mtz_filename = mtz_filename

        def get_mtz_filename(self):
            return self._mtz_filename

        def run(self):
            logger.debug("Running dials.export")

            self.clear_command_line()
            self.add_command_line(f"experiments={self._experiments_filename}")
            self.add_command_line(f"reflections={self._reflections_filename}")
            self.add_command_line(f"mtz.hklout={self._mtz_filename}")
            if self.crystal_name:
                self.add_command_line(f"mtz.crystal_name={self.crystal_name}")
            if self.project_name:
                self.add_command_line(f"mtz.project_name={self.project_name}")
            if self._combine_partials:
                self.add_command_line("combine_partials=true")
            self.add_command_line(f"partiality_threshold={self._partiality_threshold}")
            self.add_command_line(f"intensity={self._intensity_choice}")
            self.start()
            self.close_wait()
            self.check_for_errors()

    return ExportMtzWrapper()
