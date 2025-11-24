from django import forms
from django.contrib.auth.models import User
from . import models



#for admin signup
class AdminSigupForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }


#for student related form
class DoctorUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }
class DoctorForm(forms.ModelForm):
    class Meta:
        model=models.Doctor
        fields=['address','mobile','department','status','profile_pic']
        
class DoctorAppointmentForm(forms.ModelForm):
    class Meta:
        model = models.Appointment
        fields = ['patientId', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descripción de la cita...'}),
        }
    
    def __init__(self, doctor=None, *args, **kwargs):
        super(DoctorAppointmentForm, self).__init__(*args, **kwargs)
        if doctor:
            # Filtrar pacientes solo para este doctor
            self.fields['patientId'].queryset = models.Patient.objects.filter(
                assignedDoctorId=doctor.id, 
                status=True
            )
            self.fields['patientId'].label = "Paciente"
            self.fields['patientId'].empty_label = "Selecciona un paciente"



#for teacher related form
class PatientUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }
class PatientForm(forms.ModelForm):
    #this is the extrafield for linking patient and their assigend doctor
    #this will show dropdown __str__ method doctor model is shown on html so override it
    #to_field_name this will fetch corresponding value  user_id present in Doctor model and return it
    assignedDoctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Name and Department", to_field_name="user_id")
    class Meta:
        model=models.Patient
        fields=['address','mobile','status','symptoms','profile_pic']



class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=models.Doctor.objects.filter(status=True),
        empty_label="Selecciona doctor",
        label="Doctor"
    )
    patient = forms.ModelChoiceField(
        queryset=models.Patient.objects.filter(status=True),
        empty_label="Selecciona paciente", 
        label="Paciente"
    )

    class Meta:
        model = models.Appointment
        fields = ['description']


class PatientAppointmentForm(forms.ModelForm):
    doctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Doctor Name and Department", to_field_name="user_id")
    class Meta:
        model=models.Appointment
        fields=['description','status']


#for contact us page
class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

class MedicineCategoryForm(forms.ModelForm):
    class Meta:
        model = models.MedicineCategory
        fields = ['name', 'description']


class MedicineForm(forms.ModelForm):
    class Meta:
        model = models.Medicine
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del medicamento'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),  # Campo unit agregado
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class MedicineMovementForm(forms.ModelForm):
    class Meta:
        model = models.MedicineMovement
        fields = ['medicine', 'movement_type', 'quantity', 'reason', 'notes']


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = models.Prescription
        fields = ['patient', 'diagnosis', 'symptoms', 'instructions']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
        }

class PrescriptionMedicineForm(forms.ModelForm):
    class Meta:
        model = models.PrescriptionMedicine
        fields = ['medicine', 'quantity', 'dosage', 'duration']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control medicine-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1 tableta cada 8 horas'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 7 días'}),
        }
        