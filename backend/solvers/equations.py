"""Physics equation library.

Pure data — no SymPy here. Each :class:`Equation` stores the two sides of a
relation as SymPy-parseable strings plus metadata (units, fixed physical
constants, the simulation it maps to). The LLM agent never writes math; it only
*selects* an equation ``id`` from this catalog and supplies numeric values. All
actual solving happens in ``sympy_solver`` using these definitions.

Conventions
-----------
* Angles are expressed in **degrees**; expressions convert inline via
  ``*pi/180`` so a value like ``theta=45`` is used directly.
* ``units`` lists **every** symbol in the equation (variables *and* constants).
* ``constants`` are symbols auto-filled with a physical value when the caller
  does not supply one (e.g. ``g``, ``G``, ``c``, ``h``). Keeping them
  per-equation avoids name clashes (e.g. ``R`` = resistance vs. gas constant).
* Symbol names avoid Python keywords and SymPy singletons handled by the parser.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Physics domains (keep in sync with the README + /api/domains).
DOMAINS: list[str] = [
    "mechanics",
    "waves",
    "electricity",
    "thermodynamics",
    "gravitation",
    "fluids",
    "quantum",
    "relativity",
]

# Simulation templates the frontend can render.
SIMULATION_TYPES: list[str] = [
    "projectile",
    "pendulum",
    "wave",
    "circuit",
    "orbital",
    "collision",
]

DOMAIN_INFO: dict[str, dict[str, str]] = {
    "mechanics": {
        "name": "Mechanics",
        "description": "Projectile motion, Newton's laws, kinematics, energy, momentum, circular motion, collisions.",
    },
    "waves": {
        "name": "Waves & Optics",
        "description": "Wave speed, frequency/period, interference, Snell's law / refraction.",
    },
    "electricity": {
        "name": "Electricity & Circuits",
        "description": "Ohm's law, series/parallel resistors, electrical power, RC time constants.",
    },
    "thermodynamics": {
        "name": "Thermodynamics",
        "description": "Ideal & combined gas laws, heat transfer, Carnot efficiency.",
    },
    "gravitation": {
        "name": "Gravitation",
        "description": "Escape velocity, gravitational force, orbital velocity and period.",
    },
    "fluids": {
        "name": "Fluid Dynamics",
        "description": "Continuity, hydrostatic pressure, buoyancy, dynamic pressure.",
    },
    "quantum": {
        "name": "Quantum Basics",
        "description": "Photon energy, de Broglie wavelength, photoelectric effect, Bohr levels.",
    },
    "relativity": {
        "name": "Relativity Basics",
        "description": "Mass-energy, time dilation, length contraction, relativistic momentum.",
    },
}


@dataclass(frozen=True)
class Equation:
    id: str
    name: str
    domain: str
    lhs: str
    rhs: str
    description: str
    units: dict[str, str]
    constants: dict[str, float] = field(default_factory=dict)
    simulation: str | None = None
    # Optional cleaner forms for display/LaTeX (e.g. angle equations omit the
    # inline degree->radian conversion). Fall back to lhs/rhs when unset.
    display_lhs: str | None = None
    display_rhs: str | None = None

    @property
    def formula(self) -> str:
        return f"{self.lhs} = {self.rhs}"

    @property
    def display_formula(self) -> str:
        return f"{self.display_lhs or self.lhs} = {self.display_rhs or self.rhs}"

    @property
    def variables(self) -> list[str]:
        """Symbols the caller may supply or solve for (excludes fixed constants)."""
        return [s for s in self.units if s not in self.constants]

    def catalog_entry(self) -> dict:
        """Compact, prompt-friendly description for the LLM equation selector."""
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "formula": self.formula,
            "description": self.description,
            "variables": {v: self.units.get(v, "") for v in self.variables},
            "constants": list(self.constants.keys()),
            "simulation": self.simulation,
        }


# --- The library --------------------------------------------------------------

_EQUATIONS: list[Equation] = [
    # ---------------- Mechanics ----------------
    Equation(
        "projectile_range", "Projectile Range", "mechanics",
        "R", "v0**2 * sin(2*theta*pi/180) / g",
        "Horizontal range of a projectile launched on level ground.",
        {"R": "m", "v0": "m/s", "theta": "deg", "g": "m/s^2"},
        {"g": 9.81}, "projectile",
        display_rhs="v0**2 * sin(2*theta) / g",
    ),
    Equation(
        "projectile_max_height", "Projectile Maximum Height", "mechanics",
        "H", "v0**2 * sin(theta*pi/180)**2 / (2*g)",
        "Peak height reached by a projectile.",
        {"H": "m", "v0": "m/s", "theta": "deg", "g": "m/s^2"},
        {"g": 9.81}, "projectile",
        display_rhs="v0**2 * sin(theta)**2 / (2*g)",
    ),
    Equation(
        "projectile_time_of_flight", "Projectile Time of Flight", "mechanics",
        "t", "2*v0*sin(theta*pi/180) / g",
        "Total time a projectile spends in the air on level ground.",
        {"t": "s", "v0": "m/s", "theta": "deg", "g": "m/s^2"},
        {"g": 9.81}, "projectile",
        display_rhs="2*v0*sin(theta) / g",
    ),
    Equation(
        "newtons_second_law", "Newton's Second Law", "mechanics",
        "F", "m*a",
        "Net force equals mass times acceleration.",
        {"F": "N", "m": "kg", "a": "m/s^2"},
    ),
    Equation(
        "kinematic_velocity", "Kinematics: final velocity", "mechanics",
        "v", "u + a*t",
        "Final velocity under constant acceleration.",
        {"v": "m/s", "u": "m/s", "a": "m/s^2", "t": "s"},
    ),
    Equation(
        "kinematic_displacement", "Kinematics: displacement", "mechanics",
        "s", "u*t + a*t**2/2",
        "Displacement under constant acceleration.",
        {"s": "m", "u": "m/s", "t": "s", "a": "m/s^2"},
    ),
    Equation(
        "kinematic_v_squared", "Kinematics: v² = u² + 2as", "mechanics",
        "v**2", "u**2 + 2*a*s",
        "Velocity-displacement relation under constant acceleration.",
        {"v": "m/s", "u": "m/s", "a": "m/s^2", "s": "m"},
    ),
    Equation(
        "kinetic_energy", "Kinetic Energy", "mechanics",
        "KE", "m*v**2/2",
        "Translational kinetic energy.",
        {"KE": "J", "m": "kg", "v": "m/s"},
    ),
    Equation(
        "momentum", "Linear Momentum", "mechanics",
        "p", "m*v",
        "Linear momentum of a moving body.",
        {"p": "kg*m/s", "m": "kg", "v": "m/s"},
    ),
    Equation(
        "centripetal_force", "Centripetal Force", "mechanics",
        "F_c", "m*v**2/r",
        "Inward force required for circular motion.",
        {"F_c": "N", "m": "kg", "v": "m/s", "r": "m"},
    ),
    Equation(
        "pendulum_period", "Simple Pendulum Period", "mechanics",
        "T", "2*pi*sqrt(L/g)",
        "Period of a simple pendulum (small-angle approximation).",
        {"T": "s", "L": "m", "g": "m/s^2"},
        {"g": 9.81}, "pendulum",
    ),
    Equation(
        "spring_period", "Mass-Spring Period", "mechanics",
        "T", "2*pi*sqrt(m/k)",
        "Period of a mass on an ideal spring (SHM).",
        {"T": "s", "m": "kg", "k": "N/m"},
        {}, "pendulum",
    ),
    Equation(
        "elastic_collision_v1", "Elastic Collision: final velocity of body 1", "mechanics",
        "v1f", "((m1 - m2)*u1 + 2*m2*u2)/(m1 + m2)",
        "Final velocity of mass 1 after a 1-D elastic collision.",
        {"v1f": "m/s", "m1": "kg", "m2": "kg", "u1": "m/s", "u2": "m/s"},
        {}, "collision",
    ),
    Equation(
        "elastic_collision_v2", "Elastic Collision: final velocity of body 2", "mechanics",
        "v2f", "((m2 - m1)*u2 + 2*m1*u1)/(m1 + m2)",
        "Final velocity of mass 2 after a 1-D elastic collision.",
        {"v2f": "m/s", "m1": "kg", "m2": "kg", "u1": "m/s", "u2": "m/s"},
        {}, "collision",
    ),

    # ---------------- Waves & Optics ----------------
    Equation(
        "wave_speed", "Wave Speed", "waves",
        "v", "f*wavelength",
        "Wave speed equals frequency times wavelength.",
        {"v": "m/s", "f": "Hz", "wavelength": "m"},
        {}, "wave",
    ),
    Equation(
        "frequency_period", "Frequency-Period", "waves",
        "f", "1/T",
        "Frequency is the reciprocal of the period.",
        {"f": "Hz", "T": "s"},
        {}, "wave",
    ),
    Equation(
        "snells_law", "Snell's Law", "waves",
        "n1*sin(theta1*pi/180)", "n2*sin(theta2*pi/180)",
        "Refraction at an interface between two media.",
        {"n1": "", "theta1": "deg", "n2": "", "theta2": "deg"},
        display_lhs="n1*sin(theta1)", display_rhs="n2*sin(theta2)",
    ),

    # ---------------- Electricity & Circuits ----------------
    Equation(
        "ohms_law", "Ohm's Law", "electricity",
        "V", "I*R",
        "Voltage equals current times resistance.",
        {"V": "V", "I": "A", "R": "ohm"},
        {}, "circuit",
    ),
    Equation(
        "resistors_series", "Resistors in Series", "electricity",
        "R", "R1 + R2",
        "Total resistance of two resistors in series.",
        {"R": "ohm", "R1": "ohm", "R2": "ohm"},
        {}, "circuit",
    ),
    Equation(
        "resistors_parallel", "Resistors in Parallel", "electricity",
        "R", "R1*R2/(R1 + R2)",
        "Total resistance of two resistors in parallel.",
        {"R": "ohm", "R1": "ohm", "R2": "ohm"},
        {}, "circuit",
    ),
    Equation(
        "electrical_power", "Electrical Power", "electricity",
        "P", "V*I",
        "Power delivered equals voltage times current.",
        {"P": "W", "V": "V", "I": "A"},
        {}, "circuit",
    ),
    Equation(
        "power_dissipation", "Power Dissipated in a Resistor", "electricity",
        "P", "I**2*R",
        "Power dissipated by a resistor carrying current I.",
        {"P": "W", "I": "A", "R": "ohm"},
        {}, "circuit",
    ),
    Equation(
        "rc_time_constant", "RC Time Constant", "electricity",
        "tau", "R*C",
        "Time constant of a resistor-capacitor circuit.",
        {"tau": "s", "R": "ohm", "C": "F"},
    ),

    # ---------------- Thermodynamics ----------------
    Equation(
        "ideal_gas_law", "Ideal Gas Law", "thermodynamics",
        "P*V", "n*R*T",
        "Equation of state of an ideal gas (SI units).",
        {"P": "Pa", "V": "m^3", "n": "mol", "R": "J/(mol*K)", "T": "K"},
        {"R": 8.314},
    ),
    Equation(
        "combined_gas_law", "Combined Gas Law", "thermodynamics",
        "P1*V1/T1", "P2*V2/T2",
        "Relates pressure, volume and temperature of a fixed amount of gas "
        "between two states (consistent units cancel).",
        {"P1": "atm", "V1": "L", "T1": "K", "P2": "atm", "V2": "L", "T2": "K"},
    ),
    Equation(
        "carnot_efficiency", "Carnot Efficiency", "thermodynamics",
        "eta", "1 - Tc/Th",
        "Maximum efficiency of a heat engine between two reservoirs.",
        {"eta": "", "Tc": "K", "Th": "K"},
    ),
    Equation(
        "heat_transfer", "Heat Transfer", "thermodynamics",
        "Q", "m*c*dT",
        "Heat needed to change a substance's temperature by dT.",
        {"Q": "J", "m": "kg", "c": "J/(kg*K)", "dT": "K"},
    ),

    # ---------------- Gravitation ----------------
    Equation(
        "escape_velocity", "Escape Velocity", "gravitation",
        "v", "sqrt(2*G*M/r)",
        "Minimum speed to escape a body's gravity (M = body mass, r = radius).",
        {"v": "m/s", "G": "N*m^2/kg^2", "M": "kg", "r": "m"},
        {"G": 6.674e-11}, "orbital",
    ),
    Equation(
        "gravitational_force", "Newton's Law of Gravitation", "gravitation",
        "F", "G*m1*m2/r**2",
        "Gravitational attraction between two masses.",
        {"F": "N", "G": "N*m^2/kg^2", "m1": "kg", "m2": "kg", "r": "m"},
        {"G": 6.674e-11},
    ),
    Equation(
        "orbital_velocity", "Orbital Velocity", "gravitation",
        "v", "sqrt(G*M/r)",
        "Speed of a circular orbit at radius r around mass M.",
        {"v": "m/s", "G": "N*m^2/kg^2", "M": "kg", "r": "m"},
        {"G": 6.674e-11}, "orbital",
    ),
    Equation(
        "orbital_period", "Orbital Period (Kepler's Third Law)", "gravitation",
        "T", "2*pi*sqrt(r**3/(G*M))",
        "Period of a circular orbit of radius r around mass M.",
        {"T": "s", "r": "m", "G": "N*m^2/kg^2", "M": "kg"},
        {"G": 6.674e-11}, "orbital",
    ),

    # ---------------- Fluid Dynamics ----------------
    Equation(
        "continuity", "Continuity Equation", "fluids",
        "A1*v1", "A2*v2",
        "Incompressible flow: cross-section area times velocity is constant.",
        {"A1": "m^2", "v1": "m/s", "A2": "m^2", "v2": "m/s"},
    ),
    Equation(
        "hydrostatic_pressure", "Hydrostatic Pressure", "fluids",
        "P", "rho*g*h",
        "Gauge pressure at depth h in a fluid of density rho.",
        {"P": "Pa", "rho": "kg/m^3", "g": "m/s^2", "h": "m"},
        {"g": 9.81},
    ),
    Equation(
        "buoyant_force", "Buoyant Force (Archimedes)", "fluids",
        "F", "rho*Vol*g",
        "Upward buoyant force on a submerged volume Vol.",
        {"F": "N", "rho": "kg/m^3", "Vol": "m^3", "g": "m/s^2"},
        {"g": 9.81},
    ),
    Equation(
        "dynamic_pressure", "Dynamic Pressure", "fluids",
        "q", "rho*v**2/2",
        "Kinetic pressure of a fluid moving at speed v.",
        {"q": "Pa", "rho": "kg/m^3", "v": "m/s"},
    ),

    # ---------------- Quantum Basics ----------------
    Equation(
        "photon_energy", "Photon Energy", "quantum",
        "E", "h*f",
        "Energy of a photon of frequency f.",
        {"E": "J", "h": "J*s", "f": "Hz"},
        {"h": 6.626e-34},
    ),
    Equation(
        "de_broglie", "de Broglie Wavelength", "quantum",
        "wavelength", "h/(m*v)",
        "Matter wavelength of a particle of mass m moving at speed v.",
        {"wavelength": "m", "h": "J*s", "m": "kg", "v": "m/s"},
        {"h": 6.626e-34},
    ),
    Equation(
        "photoelectric", "Photoelectric Effect", "quantum",
        "KE", "h*f - phi",
        "Max kinetic energy of an ejected electron (phi = work function).",
        {"KE": "J", "h": "J*s", "f": "Hz", "phi": "J"},
        {"h": 6.626e-34},
    ),
    Equation(
        "bohr_energy", "Bohr Energy Level", "quantum",
        "E", "-13.6/n**2",
        "Energy of the nth level of the hydrogen atom (in eV).",
        {"E": "eV", "n": ""},
    ),

    # ---------------- Relativity Basics ----------------
    Equation(
        "mass_energy", "Mass-Energy Equivalence", "relativity",
        "E", "m*c**2",
        "Rest energy of a mass m.",
        {"E": "J", "m": "kg", "c": "m/s"},
        {"c": 2.998e8},
    ),
    Equation(
        "time_dilation", "Time Dilation", "relativity",
        "t", "t0/sqrt(1 - v**2/c**2)",
        "Dilated time interval for a clock moving at speed v.",
        {"t": "s", "t0": "s", "v": "m/s", "c": "m/s"},
        {"c": 2.998e8},
    ),
    Equation(
        "length_contraction", "Length Contraction", "relativity",
        "L", "L0*sqrt(1 - v**2/c**2)",
        "Contracted length of an object moving at speed v.",
        {"L": "m", "L0": "m", "v": "m/s", "c": "m/s"},
        {"c": 2.998e8},
    ),
    Equation(
        "relativistic_momentum", "Relativistic Momentum", "relativity",
        "p", "m*v/sqrt(1 - v**2/c**2)",
        "Momentum of a mass m moving at relativistic speed v.",
        {"p": "kg*m/s", "m": "kg", "v": "m/s", "c": "m/s"},
        {"c": 2.998e8},
    ),
]

# Public lookup helpers -------------------------------------------------------

EQUATIONS: dict[str, Equation] = {eq.id: eq for eq in _EQUATIONS}


def get_equation(equation_id: str) -> Equation:
    try:
        return EQUATIONS[equation_id]
    except KeyError as exc:
        raise KeyError(f"Unknown equation id: {equation_id!r}") from exc


def equations_for_domain(domain: str) -> list[Equation]:
    return [eq for eq in _EQUATIONS if eq.domain == domain]


def catalog(domain: str | None = None) -> list[dict]:
    """Prompt-friendly catalog, optionally filtered to one domain."""
    eqs = equations_for_domain(domain) if domain else _EQUATIONS
    return [eq.catalog_entry() for eq in eqs]


# Useful, commonly-referenced physical values the extractor can fill in.
NAMED_CONSTANTS: dict[str, float] = {
    "earth_mass": 5.972e24,
    "earth_radius": 6.371e6,
    "moon_mass": 7.342e22,
    "moon_radius": 1.737e6,
    "sun_mass": 1.989e30,
    "speed_of_light": 2.998e8,
    "gravitational_constant": 6.674e-11,
    "planck_constant": 6.626e-34,
    "gas_constant": 8.314,
}
