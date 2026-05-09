import re
from typing import Callable, Iterable, Optional
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional as OptionalValidator,
    ValidationError,
)

ExistsFn = Callable[[str], bool]


class AllowedSpecialChars:
    """
    Validador  de caracteres especiales
    """

    _alnum_es_pattern = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s]+$"

    def __init__(
        self,
        allow_special: bool = False,
    ):
        """_summary_
        Inicializa el validador de caracteres especiales

        Args:
            allow_special (bool, optional): Si se permiten caracteres especiales.
        """
        self.allow_special = allow_special
        self.message = "No se permiten caracteres especiales."

    def __call__(self, form, field):
        """_summary_
        Valida que el campo no contenga caracteres especiales si allow_special es False

        Args:
            form: Formulario
            field: Campo a validar

        Raises:
            ValidationError: Si el campo contiene caracteres especiales y no están permitidos
        """
        value = field.data or ""
        if (
            re.search(r"[^\w\sÁÉÍÓÚÜÑáéíóúüñ]", value, flags=re.UNICODE)
        ) and not self.allow_special:
            raise ValidationError(self.message)


class Unique:
    """
    Validar unicidad
    """

    def __init__(
        self, exists_fn: ExistsFn, message: str = "El valor ya está registrado."
    ):
        """_summary_
        Inicializa el validador de unicidad

        Args:
            exists_fn (ExistsFn): Funcion que verifica si el valor existe
            message (str, optional): Mensaje de error. Default: "El valor ya está registrado."
        """
        self.exists_fn = exists_fn
        self.message = message
        self.normalizer = lambda s: s.strip().lower()

    def __call__(self, form, field):
        """_summary_
        Valida que el valor del campo sea unico

        Args:
            form: Formulario
            field: Campo a validar

        Raises:
            ValidationError: Si el valor ya existe
        """
        raw = field.data
        value = "" if raw is None else str(raw)
        value = self.normalizer(value)
        if self.exists_fn(value):
            raise ValidationError(self.message)


class Validators:
    """
    Validadores
    """

    @staticmethod
    def required(field: str):
        """_summary_
        Validador de campo obligatorio

        Args:
            field (str): Nombre del campo

        Returns:
            DataRequired: Validador de campo obligatorio
        """
        return DataRequired(message=f"El campo {field} es obligatorio.")

    @staticmethod
    def optional():
        """_summary_
        Validador de campo opcional

        Returns:
            OptionalValidator: Validador de campo opcional
        """
        return OptionalValidator()

    @staticmethod
    def length(
        min: Optional[int] = None,
        max: Optional[int] = None,
        field: Optional[str] = None,
    ):
        """_summary_
        Validador de longitud de campo

        Args:
            min (Optional[int], optional): Longitud minima. Defaults to None.
            max (Optional[int], optional): Longitud maxima. Defaults to None.
            field (Optional[str], optional): Nombre del campo. Defaults to None.

        Returns:
            Length: Validador de longitud

        Raises:
            ValidationError: Si min y max son None
        """
        if min is None and max is None:
            raise ValidationError("Debes definir al menos un valor para min o max.")

        if min is not None and max is not None:
            message = f"{field} debe tener entre {min} y {max} caracteres."
        elif min is not None:
            message = f"{field} debe tener al menos {min} caracteres."
        else:
            message = f"{field} debe tener como máximo {max} caracteres."

        kwargs = {"message": message}
        if min is not None:
            kwargs["min"] = min
        if max is not None:
            kwargs["max"] = max

        return Length(**kwargs)

    @staticmethod
    def email(message: str = "Formato de email inválido."):
        """_summary_
        Validador de formato de email

        Args:
            message (str, optional): Mensaje de error. Default: "Formato de email inválido."

        Returns:
            Email: Validador de email
        """
        return Email(message=message)

    @staticmethod
    def number_range(
        min: Optional[float] = None,
        max: Optional[float] = None,
        field: Optional[str] = None,
    ):
        """_summary_
        Validador de rango numerico

        Args:
            min (Optional[float], optional): Valor minimo. Default: None.
            max (Optional[float], optional): Valor maximo. Default: None.
            field (Optional[str], optional): Nombre del campo. Default: None.

        Returns:
            NumberRange: Validador de rango numerico

        Raises:
            ValidationError: Si min y max son None
        """
        if isinstance(min, str):
            min = float(min)
        if isinstance(max, str):
            max = float(max)

        message = ""
        if min == None and max == None:
            raise ValidationError(
                "Min y max no pueden ser nulos al mismo tiempo, debe setear al menos uno."
            )
        elif min == None:
            message = f"{field} debe tener un numero menor o igual a {max}."
        elif max == None:
            message = f"{field} debe tener un numero mayor o igual a {min}."
        else:
            message = f"{field} debe ser un número entre {min} y {max}"
        return NumberRange(min=min, max=max, message=message)

    @staticmethod
    def allowed_chars(
        allow_special: bool = False,
    ):
        """_summary_
        Validador de caracteres permitidos

        Args:
            allow_special (bool, optional): Si se permiten caracteres especiales. Default: False.

        Returns:
            AllowedSpecialChars: Validador de caracteres permitidos
        """
        return AllowedSpecialChars(allow_special=allow_special)

    @staticmethod
    def unique(
        exists_fn: ExistsFn,
        message: str = "",
    ):
        """_summary_
        Validador de unicidad

        Args:
            exists_fn (ExistsFn): Funcion que verifica si el valor existe
            message (str, optional): Mensaje de error. Default: "".

        Returns:
            Unique: Validador de unicidad
        """
        return Unique(exists_fn=exists_fn, message=message)

    @staticmethod
    def unique_ignore_current(exists_fn, id_form, field_name=""):
        """
        Validador de unicidad en campo de actualizar, evita que se cambie en el html el valor que esta griseado, compara el actual con el de la db.
        """

        def _validator(form, field):
            entity = exists_fn(field.data)
            if entity:
                current_id = id_form(form)
                if getattr(entity, "id", None) != current_id:
                    raise ValidationError(f"Ya existe un registro con {field_name}.")

        return _validator

    @staticmethod
    def equal_to(fieldname: str, message: Optional[str] = None):
        """
        Validador que compara que dos campos sean iguales.
        """
        if message is None:
            message = "Los campos deben coincidir."
        return EqualTo(fieldname, message=message)


def build_validators(specs: Iterable) -> list:
    """_summary_
    Construye una lista de validadores.

    Args:
        specs (Iterable): Iterable de validadores

    Returns:
        list: Lista de validadores
    """
    return list(specs)
