import csv

from bootstrap_datepicker_plus import DatePickerInput
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django_measurement.forms import MeasurementField
from measurement.measures import Distance, Weight
from cloudinary.forms import CloudinaryFileField

from .models import Log, Setting, Image


class MeasurementWidget(forms.MultiWidget):
    def __init__(
        self,
        float_widget=None,
        unit_choices_widget=None,
        unit_choices=None,
        *args,
        **kwargs
    ):

        self.unit_choices = unit_choices

        if not float_widget:
            float_widget = forms.TextInput(
                attrs={
                    "class": "form-control",
                    "style": "width: 55%; display: inline-block;",
                    "placeholder": "160",
                }
            )

        if not unit_choices_widget:
            unit_choices_widget = forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width: 20%; display: inline-block;",
                    "placeholder": "160",
                },
                choices=unit_choices,
            )

        widgets = (float_widget, unit_choices_widget)
        super(MeasurementWidget, self).__init__(widgets)

    def decompress(self, value):
        if value:
            choice_units = set([u for u, n in self.unit_choices])

            unit = value.STANDARD_UNIT
            if unit not in choice_units:
                unit = choice_units.pop()

            magnitude = getattr(value, unit)
            return [magnitude, unit]

        return [None, None]


class RegisterForm(UserCreationForm):

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-user", "placeholder": "Password"}
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-user",
                "placeholder": "Repeat Password",
            }
        )
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
        )

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control form-control-user",
                    "placeholder": "Username",
                }
            ),
            "email": forms.TextInput(
                attrs={
                    "class": "form-control form-control-user",
                    "placeholder": "Email Address  *Optional",
                }
            ),
        }


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control form-control-user", "placeholder": "Username"}
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-user", "placeholder": "Password"}
        )
    )


class ImportCSVForm(forms.Form):

    data_file = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "style": "display: inline-block;",
                "accept": ".csv",
            },
        ),
        required=True,
    )

    weight_units = forms.ChoiceField(
        label="What unit is your weight data in?",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=(("lb", "lbs"), ("kg", "kgs")),
        required=True,
    )

    date_format = forms.ChoiceField(
        label="Please specify your date format (Year is optional; will default to the current year)",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=[
            ("MDY", "Month, Day, Year"),
            ("DMY", "Day, Month, Year"),
            ("YMD", "Year, Month, Day"),
            ("YDM", "Year, Day, Month"),
        ],
        required=True,
    )

    csv_overwrite = forms.ChoiceField(
        label="Overwrite existing log entries?",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=[
            ("True", "Yes, overwrite any log entries I have"),
            ("False", "No, don't overwrite my log entries"),
        ],
        required=True,
    )


class ImportMFPForm(forms.Form):
    mfp_start_date = forms.DateField(
        label="Please select your import START date",
        widget=DatePickerInput(
            attrs={
                "style": "display: inline-block;",
            },
        ),
        required=True,
    )
    mfp_end_date = forms.DateField(
        label="Please select your import END date",
        widget=DatePickerInput(
            attrs={
                "style": "display: inline-block;",
            },
        ),
        required=True,
    )
    mfp_data_select = forms.ChoiceField(
        label="Which data would you like to import?",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=[
            ("Weights", "MFP Weight Entries"),
            ("CI", "MFP Caloric Intake Logs"),
        ],
        required=True,
    )
    mfp_overwrite = forms.ChoiceField(
        label="Overwrite existing log entries?",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=[
            ("True", "Yes, overwrite any log entries I have"),
            ("False", "No, don't overwrite my log entries"),
        ],
        required=True,
    )


class LogDataForm(forms.ModelForm):
    class Meta:
        model = Log
        fields = (
            "date",
            "weight",
            "calories_in",
            "calories_out",
            "activity_lvl",
            "front_progress_pic",
            "side_progress_pic",
            "back_progress_pic"

        )

    front_progress_pic = CloudinaryFileField(
        label="Front Facing Progress Pic:",
        widget=forms.FileInput(
            attrs={
                "style": "display: inline-block;",
            }
        ),
        options={
            "folder": "progress_pics",
        },
        required=False,
    )

    side_progress_pic = CloudinaryFileField(
        label="Side Facing Progress Pic:",
        widget=forms.FileInput(
            attrs={
                "style": "display: inline-block;",
            }
        ),
        options={
            "folder": "progress_pics",
        },
        required=False,
    )

    back_progress_pic = CloudinaryFileField(
        label="Back Facing Progress Pic:",
        widget=forms.FileInput(
            attrs={
                "style": "display: inline-block;",
            }
        ),
        options={
            "folder": "progress_pics",
        },
        required=False,
    )

    date = forms.DateField(
        widget=DatePickerInput(
            attrs={
                "style": "display: inline-block;",
            },
        ),
        required=True,
    )

    weight = MeasurementField(
        widget=MeasurementWidget(
            unit_choices=(("lb", "lbs"), ("kg", "kgs")),
        ),
        measurement=Weight,
        required=True,
    )

    calories_in = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
                "placeholder": "2000",
            }
        ),
        required=True,
    )

    calories_out = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            }
        ),
        required=False,
    )

    activity_lvl = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=Log.choices,
        required=False,
    )


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = [
            "age",
            "sex",
            "height",
            "activity",
            "goal",
            "goal_weight",
            "goal_date",
            "unit_preference",
        ]

    goal_weight = MeasurementField(
        widget=MeasurementWidget(
            unit_choices=(("lb", "lbs"), ("kg", "kgs")),
        ),
        measurement=Weight,
        required=True,
    )

    goal_date = forms.DateField(
        widget=DatePickerInput(
            attrs={
                "style": "display: inline-block;",
            },
        ),
        required=True,
    )

    goal = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=Setting.goal_choices,
        required=True,
    )

    unit_preference = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=Setting.unit_choices,
        required=True,
    )

    age = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
                "placeholder": "30",
            }
        ),
        required=True,
    )

    sex = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=Setting.sex_choices,
        required=True,
    )

    height = MeasurementField(
        widget=MeasurementWidget(
            unit_choices=(("inch", "in"), ("cm", "cm")),
        ),
        measurement=Distance,
        required=True,
    )

    activity = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "style": "display: inline-block;",
            },
        ),
        choices=Setting.activity_choices,
        required=True,
    )
