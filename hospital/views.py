from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.conf import settings
from django.db.models import Q

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/index.html')


def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/adminclick.html')


def doctorclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/doctorclick.html')


def patientclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/patientclick.html')




def admin_signup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()
            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)
            return HttpResponseRedirect('adminlogin')
    return render(request,'hospital/adminsignup.html',{'form':form})




def doctor_signup_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST,request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor=doctor.save()
            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)
        return HttpResponseRedirect('doctorlogin')
    return render(request,'hospital/doctorsignup.html',context=mydict)


def patient_signup_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.user=user
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient=patient.save()
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
        return HttpResponseRedirect('patientlogin')
    return render(request,'hospital/patientsignup.html',context=mydict)






#-----------for checking user is doctor , patient or admin(by sumit)
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()
def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,DOCTOR OR PATIENT
def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_doctor(request.user):
        accountapproval=models.Doctor.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('doctor-dashboard')
        else:
            return render(request,'hospital/doctor_wait_for_approval.html')
    elif is_patient(request.user):
        accountapproval=models.Patient.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('patient-dashboard')
        else:
            return render(request,'hospital/patient_wait_for_approval.html')



#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    #for both table in admin dashboard
    doctors=models.Doctor.objects.all().order_by('-id')
    patients=models.Patient.objects.all().order_by('-id')
    
    #for three cards - CORREGIDO
    doctorcount=models.Doctor.objects.all().filter(status=True).count()
    pendingdoctorcount=models.Doctor.objects.all().filter(status=False).count()

    patientcount=models.Patient.objects.all().filter(status=True).count()
    pendingpatientcount=models.Patient.objects.all().filter(status=False).count()

    # CONTADORES DE CITAS CORREGIDOS
    appointmentcount=models.Appointment.objects.all().count()  # Todas las citas
    pendingappointmentcount=models.Appointment.objects.all().filter(status='pending').count()  # Solo pendientes
    
    mydict={
    'doctors':doctors,
    'patients':patients,
    'doctorcount':doctorcount,
    'pendingdoctorcount':pendingdoctorcount,
    'patientcount':patientcount,
    'pendingpatientcount':pendingpatientcount,
    'appointmentcount':appointmentcount,  # Total de citas
    'pendingappointmentcount':pendingappointmentcount,  # Citas pendientes
    }
    return render(request,'hospital/admin_dashboard.html',context=mydict)


# this view for sidebar click on admin page
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    return render(request,'hospital/admin_doctor.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    messages.success(request, '✅ Doctor eliminado exitosamente!')
    return redirect('admin-view-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)

    userForm=forms.DoctorUserForm(instance=user)
    doctorForm=forms.DoctorForm(request.FILES,instance=doctor)
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST,instance=user)
        doctorForm=forms.DoctorForm(request.POST,request.FILES,instance=doctor)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.status=True
            doctor.save()
            messages.success(request, '✅ Doctor actualizado exitosamente!')
            return redirect('admin-view-doctor')
        else:
            messages.error(request, '❌ Error en el formulario. Por favor verifica los datos.')
    return render(request,'hospital/admin_update_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor.status=True
            doctor.save()

            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)

            messages.success(request, '✅ Doctor agregado exitosamente!')
            return HttpResponseRedirect('admin-view-doctor')
        else:
            messages.error(request, '❌ Error en el formulario. Por favor verifica los datos.')
    return render(request,'hospital/admin_add_doctor.html',context=mydict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    #those whose approval are needed
    doctors=models.Doctor.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_doctor.html',{'doctors':doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    doctor.status=True
    doctor.save()
    return redirect(reverse('admin-approve-doctor'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-approve-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor_specialisation.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    return render(request,'hospital/admin_patient.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-view-patient')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)

    userForm=forms.PatientUserForm(instance=user)
    patientForm=forms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST,instance=user)
        patientForm=forms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()
            return redirect('admin-view-patient')
    return render(request,'hospital/admin_update_patient.html',context=mydict)





@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            patient=patientForm.save(commit=False)
            patient.user=user
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()

            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-patient')
    return render(request,'hospital/admin_add_patient.html',context=mydict)



#------------------FOR APPROVING PATIENT BY ADMIN----------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    #those whose approval are needed
    patients=models.Patient.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    patient.status=True
    patient.save()
    return redirect(reverse('admin-approve-patient'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-approve-patient')



#--------------------- FOR DISCHARGING PATIENT BY ADMIN START-------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_discharge_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    days=(date.today()-patient.admitDate) #2 days, 0:00:00
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
    d=days.days # only how many day that is 2
    patientDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'day':d,
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        feeDict ={
            'roomCharge':int(request.POST['roomCharge'])*int(d),
            'doctorFee':request.POST['doctorFee'],
            'medicineCost' : request.POST['medicineCost'],
            'OtherCharge' : request.POST['OtherCharge'],
            'total':(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        }
        patientDict.update(feeDict)
        #for updating to database patientDischargeDetails (pDD)
        pDD=models.PatientDischargeDetails()
        pDD.patientId=pk
        pDD.patientName=patient.get_name
        pDD.assignedDoctorName=assignedDoctor[0].first_name
        pDD.address=patient.address
        pDD.mobile=patient.mobile
        pDD.symptoms=patient.symptoms
        pDD.admitDate=patient.admitDate
        pDD.releaseDate=date.today()
        pDD.daySpent=int(d)
        pDD.medicineCost=int(request.POST['medicineCost'])
        pDD.roomCharge=int(request.POST['roomCharge'])*int(d)
        pDD.doctorFee=int(request.POST['doctorFee'])
        pDD.OtherCharge=int(request.POST['OtherCharge'])
        pDD.total=(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        pDD.save()
        return render(request,'hospital/patient_final_bill.html',context=patientDict)
    return render(request,'hospital/patient_generate_bill.html',context=patientDict)



#--------------for discharge patient bill (pdf) download and printing
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return



def download_pdf_view(request,pk):
    dischargeDetails=models.PatientDischargeDetails.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':dischargeDetails[0].patientName,
        'assignedDoctorName':dischargeDetails[0].assignedDoctorName,
        'address':dischargeDetails[0].address,
        'mobile':dischargeDetails[0].mobile,
        'symptoms':dischargeDetails[0].symptoms,
        'admitDate':dischargeDetails[0].admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
    }
    return render_to_pdf('hospital/download_bill.html',dict)



#-----------------APPOINTMENT START--------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    return render(request,'hospital/admin_appointment.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments = models.Appointment.objects.all().order_by('-id')
    print(f"DEBUG: Encontradas {appointments.count()} citas")  # Debug
    for appointment in appointments:
        print(f"DEBUG: Cita - Doctor: {appointment.doctorName}, Paciente: {appointment.patientName}, Estado: {appointment.status}")
    
    return render(request, 'hospital/admin_view_appointment.html', {'appointments': appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    appointmentForm = forms.AppointmentForm()
    mydict = {'appointmentForm': appointmentForm}
    
    if request.method == 'POST':
        appointmentForm = forms.AppointmentForm(request.POST)
        if appointmentForm.is_valid():
            appointment = appointmentForm.save(commit=False)
            
            # Obtener doctor y paciente del formulario
            doctor = appointmentForm.cleaned_data['doctor']
            patient = appointmentForm.cleaned_data['patient']
            appointment.doctorId = doctor.id
            appointment.patientId = patient.id
            appointment.doctorName = doctor.get_name
            appointment.patientName = patient.get_name
            appointment.status = 'pending'  # ← CAMBIAR A 'pending'
            
            appointment.save()
            return redirect('admin-view-appointment')
    
    return render(request, 'hospital/admin_add_appointment.html', context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    #those whose approval are needed
    appointments=models.Appointment.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.status=True
    appointment.save()
    return redirect(reverse('admin-approve-appointment'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    return redirect('admin-approve-appointment')
#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    #for three cards
    patientcount=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).count()
    appointmentcount=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).count()
    patientdischarged=models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name).count()

    #for  table in doctor dashboard
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).order_by('-id')
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid).order_by('-id')
    appointments=zip(appointments,patients)
    mydict={
    'patientcount':patientcount,
    'appointmentcount':appointmentcount,
    'patientdischarged':patientdischarged,
    'appointments':appointments,
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_dashboard.html',context=mydict)



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    mydict={
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_patient.html',context=mydict)


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_add_appointment_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    
    # Obtener solo los pacientes asignados a este doctor
    my_patients = models.Patient.objects.filter(assignedDoctorId=doctor.user_id, status=True)
    
    if request.method == 'POST':
        description = request.POST.get('description')
        patient_id = request.POST.get('patientId')
        
        try:
            patient = models.Patient.objects.get(id=patient_id)
            
            # Crear la cita
            appointment = models.Appointment(
                doctorId=doctor.id,
                patientId=patient.id,
                doctorName=doctor.get_name,
                patientName=patient.get_name,
                description=description,
                status='pending'
            )
            appointment.save()
            
            messages.success(request, f'✅ Cita agendada exitosamente con {patient.get_name}')
            return redirect('doctor-view-appointment')
            
        except models.Patient.DoesNotExist:
            messages.error(request, "❌ Paciente no encontrado")
        except Exception as e:
            messages.error(request, f"❌ Error al agendar cita: {str(e)}")
    
    return render(request, 'hospital/doctor_add_appointment.html', {
        'doctor': doctor,
        'my_patients': my_patients
    })


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    # whatever user write in search box we get in query
    query = request.GET['query']
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).filter(Q(symptoms__icontains=query)|Q(user__first_name__icontains=query))
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    dischargedpatients=models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_discharge_patient.html',{'dischargedpatients':dischargedpatients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_appointment.html',{'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    
    # Filtrar citas por el ID del doctor actual
    appointments = models.Appointment.objects.filter(
        doctorId=doctor.id
    ).order_by('-appointmentDate')
    
    # Obtener información de pacientes y verificar recetas
    appointment_data = []
    for appointment in appointments:
        try:
            patient = models.Patient.objects.get(id=appointment.patientId)
            
            # VERIFICACIÓN DIRECTA: Usar el campo prescription
            has_prescription = appointment.prescription is not None
            
            # DEBUG: Mostrar en consola para verificar
            print(f"Cita {appointment.id} - Paciente: {patient.get_name} - Receta: {has_prescription}")
            if has_prescription:
                print(f"   Receta ID: {appointment.prescription.id}")
            
            appointment_data.append({
                'appointment': appointment,
                'patient': patient,
                'has_prescription': has_prescription
            })
        except models.Patient.DoesNotExist:
            continue
    
    return render(request, 'hospital/doctor_view_appointment.html', {
        'appointment_data': appointment_data, 
        'doctor': doctor
    })

from django.contrib import messages

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def update_appointment_status_view(request, pk, status):
    try:
        appointment = models.Appointment.objects.get(id=pk)
        doctor = models.Doctor.objects.get(user_id=request.user.id)
        
        # Verificar que la cita pertenece al doctor actual
        if appointment.doctorId == doctor.id:
            if status in ['done', 'cancelled', 'pending']:
                appointment.status = status
                appointment.save()
                
                # Mensajes según la acción
                if status == 'done':
                    messages.success(request, f'✅ Cita de {appointment.patientName} marcada como ATENDIDA')
                elif status == 'cancelled':
                    messages.warning(request, f'❌ Cita de {appointment.patientName} CANCELADA')
                elif status == 'pending':
                    messages.info(request, f'🔄 Cita de {appointment.patientName} reactivada como PENDIENTE')
            else:
                messages.error(request, "Estado no válido")
        else:
            messages.error(request, "No tienes permiso para modificar esta cita")
            
    except models.Appointment.DoesNotExist:
        messages.error(request, "Cita no encontrada")
    except models.Doctor.DoesNotExist:
        messages.error(request, "Doctor no encontrado")
    
    return redirect('doctor-view-appointment')


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})



#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ PATIENT RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id)
    doctor=models.Doctor.objects.get(user_id=patient.assignedDoctorId)
    mydict={
    'patient':patient,
    'doctorName':doctor.get_name,
    'doctorMobile':doctor.mobile,
    'doctorAddress':doctor.address,
    'symptoms':patient.symptoms,
    'doctorDepartment':doctor.department,
    'admitDate':patient.admitDate,
    }
    return render(request,'hospital/patient_dashboard.html',context=mydict)



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_appointment.html',{'patient':patient})



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_book_appointment_view(request):
    appointmentForm=forms.PatientAppointmentForm()
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    message=None
    mydict={'appointmentForm':appointmentForm,'patient':patient,'message':message}
    if request.method=='POST':
        appointmentForm=forms.PatientAppointmentForm(request.POST)
        if appointmentForm.is_valid():
            print(request.POST.get('doctorId'))
            desc=request.POST.get('description')

            doctor=models.Doctor.objects.get(user_id=request.POST.get('doctorId'))
            
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.user.id #----user can choose any patient but only their info will be stored
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=request.user.first_name #----user can choose any patient but only their info will be stored
            appointment.status=False
            appointment.save()
        return HttpResponseRedirect('patient-view-appointment')
    return render(request,'hospital/patient_book_appointment.html',context=mydict)



def patient_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})



def search_doctor_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    
    # whatever user write in search box we get in query
    query = request.GET['query']
    doctors=models.Doctor.objects.all().filter(status=True).filter(Q(department__icontains=query)| Q(user__first_name__icontains=query))
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})




@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    patient = models.Patient.objects.get(user_id=request.user.id)
    
    # Filtrar citas por el ID del paciente actual
    appointments = models.Appointment.objects.filter(
        patientId=patient.id
    ).order_by('-appointmentDate')
    
    return render(request, 'hospital/patient_view_appointment.html', {
        'appointments': appointments, 
        'patient': patient
    })



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    dischargeDetails=models.PatientDischargeDetails.objects.all().filter(patientId=patient.id).order_by('-id')[:1]
    patientDict=None
    if dischargeDetails:
        patientDict ={
        'is_discharged':True,
        'patient':patient,
        'patientId':patient.id,
        'patientName':patient.get_name,
        'assignedDoctorName':dischargeDetails[0].assignedDoctorName,
        'address':patient.address,
        'mobile':patient.mobile,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
        }
        print(patientDict)
    else:
        patientDict={
            'is_discharged':False,
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_discharge.html',context=patientDict)


#------------------------ PATIENT RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START ------------------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'hospital/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'hospital/contactussuccess.html')
    return render(request, 'hospital/contactus.html', {'form':sub})


#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_medicine_view(request):
    # Calcular estadísticas
    total_medicines = models.Medicine.objects.count()
    
    # Medicamentos con stock bajo (menos de 20 unidades)
    low_stock = models.Medicine.objects.filter(stock_quantity__lt=20, stock_quantity__gt=0).count()
    
    # Medicamentos agotados (stock = 0)
    out_of_stock = models.Medicine.objects.filter(stock_quantity=0).count()
    
    # Medicamentos próximos a vencer (en los próximos 30 días)
    today = date.today()
    next_month = today + timedelta(days=30)
    expired_soon = models.Medicine.objects.filter(
        expiry_date__range=[today, next_month]
    ).count()
    
    context = {
        'total_medicines': total_medicines,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'expired_soon': expired_soon,
    }
    
    return render(request, 'hospital/admin_medicine.html', context)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_medicine_view(request):
    medicines = models.Medicine.objects.all().order_by('name')
    return render(request, 'hospital/admin_view_medicine.html', {'medicines': medicines})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_medicine_view(request):
    medicineForm = forms.MedicineForm()
    
    if request.method == 'POST':
        medicineForm = forms.MedicineForm(request.POST)
        if medicineForm.is_valid():
            medicine = medicineForm.save()
            
            # Registrar movimiento inicial
            models.MedicineMovement.objects.create(
                medicine=medicine,
                movement_type='entrada',
                quantity=medicine.stock_quantity,
                previous_stock=0,
                new_stock=medicine.stock_quantity,
                reason='Stock inicial',
                performed_by=request.user
            )
            
            messages.success(request, f'Medicamento {medicine.name} agregado exitosamente')
            return redirect('admin-view-medicine')
    
    return render(request, 'hospital/admin_add_medicine.html', {'medicineForm': medicineForm})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_update_medicine_view(request, pk):
    medicine = models.Medicine.objects.get(id=pk)
    medicineForm = forms.MedicineForm(instance=medicine)
    
    if request.method == 'POST':
        medicineForm = forms.MedicineForm(request.POST, instance=medicine)
        if medicineForm.is_valid():
            medicineForm.save()
            messages.success(request, f'Medicamento {medicine.name} actualizado')
            return redirect('admin-view-medicine')
    
    return render(request, 'hospital/admin_update_medicine.html', {
        'medicineForm': medicineForm,
        'medicine': medicine
    })

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_medicine_movement_view(request, pk):
    medicine = models.Medicine.objects.get(id=pk)
    movements = models.MedicineMovement.objects.filter(medicine=medicine).order_by('-movement_date')
    
    if request.method == 'POST':
        movement_type = request.POST.get('movement_type')
        quantity = int(request.POST.get('quantity'))
        reason = request.POST.get('reason')
        notes = request.POST.get('notes')
        
        previous_stock = medicine.stock_quantity
        
        # Crear movimiento
        movement = models.MedicineMovement(
            medicine=medicine,
            movement_type=movement_type,
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=previous_stock + quantity if movement_type == 'entrada' else previous_stock - quantity,
            reason=reason,
            performed_by=request.user,
            notes=notes
        )
        movement.save()
        
        messages.success(request, f'Movimiento registrado para {medicine.name}')
        return redirect('admin-medicine-movement', pk=pk)
    
    return render(request, 'hospital/admin_medicine_movement.html', {
        'medicine': medicine,
        'movements': movements
    })

# Vistas para Doctor
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_medicine_view(request):
    medicines = models.Medicine.objects.filter(is_active=True).order_by('name')
    low_stock = medicines.filter(stock_quantity__lte=models.F('min_stock'))
    expired = medicines.filter(expiry_date__lt=date.now().date())
    
    return render(request, 'hospital/doctor_medicine.html', {
        'medicines': medicines,
        'low_stock': low_stock,
        'expired': expired
    })
    
from django.shortcuts import render, get_object_or_404, redirect 
from .models import Medicine
@login_required
def admin_delete_medicine_view(request, pk):
    medicine = get_object_or_404(Medicine, id=pk)
    
    if request.method == 'POST':
        try:
            medicine_name = medicine.name
            medicine.delete()
            messages.success(request, f'Medicamento {medicine_name} eliminado exitosamente!')
            return redirect('admin-view-medicine')
        except Exception as e:
            messages.error(request, f'Error al eliminar medicamento: {str(e)}')
    
    return render(request, 'hospital/admin_delete_medicine.html', {'medicine': medicine})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_low_stock_medicine_view(request):
    # Medicamentos con stock bajo (menos de 20 unidades pero mayor a 0)
    low_stock_medicines = models.Medicine.objects.filter(
        stock_quantity__lt=20, 
        stock_quantity__gt=0
    ).order_by('stock_quantity')
    
    return render(request, 'hospital/admin_low_stock_medicine.html', {
        'medicines': low_stock_medicines
    })
    
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_out_of_stock_medicine_view(request):
    # Medicamentos con stock = 0
    out_of_stock_medicines = models.Medicine.objects.filter(
        stock_quantity=0
    ).order_by('name')
    
    return render(request, 'hospital/admin_out_of_stock_medicine.html', {
        'medicines': out_of_stock_medicines
    })
    
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_prescription_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    return render(request, 'hospital/doctor_prescription.html', {'doctor': doctor})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_create_prescription_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    
    # Obtener paciente desde la URL si viene de una cita
    patient_id = request.GET.get('patient_id')
    appointment_id = request.GET.get('appointment_id')
    
    # Solo pacientes asignados a este doctor
    my_patients = models.Patient.objects.filter(assignedDoctorId=doctor.user_id, status=True)
    
    # CARGAR TODOS LOS MEDICAMENTOS SIN FILTROS
    medicines = models.Medicine.objects.all().order_by('name')
    
    if request.method == 'POST':
        try:
            print("DEBUG: Iniciando creación de receta...")
            
            # Validar que se haya seleccionado un paciente
            patient_id_post = request.POST.get('patient')
            if not patient_id_post:
                messages.error(request, '❌ Debe seleccionar un paciente')
                return redirect('doctor-create-prescription')
            
            # Crear la receta
            prescription = models.Prescription(
                patient_id=patient_id_post,
                doctor=doctor,
                diagnosis=request.POST.get('diagnosis', ''),
                symptoms=request.POST.get('symptoms', ''),
                instructions=request.POST.get('instructions', '')
            )
            prescription.save()
            print(f"DEBUG: Receta #{prescription.id} creada")
            
            # Procesar medicamentos
            medicine_ids = request.POST.getlist('medicines[]')
            quantities = request.POST.getlist('quantities[]')
            dosages = request.POST.getlist('dosages[]')
            durations = request.POST.getlist('durations[]')
            
            print(f"DEBUG: Medicamentos a procesar: {len(medicine_ids)}")
            
            # Validar que haya al menos un medicamento
            if not medicine_ids or not any(medicine_ids):
                prescription.delete()
                messages.error(request, '❌ Debe agregar al menos un medicamento a la receta')
                return redirect('doctor-create-prescription')
            
            # Validar TODOS los medicamentos antes de crear cualquier PrescriptionMedicine
            for i in range(len(medicine_ids)):
                if medicine_ids[i] and quantities[i]:
                    try:
                        medicine = models.Medicine.objects.get(id=medicine_ids[i])
                        quantity = int(quantities[i])
                        
                        # Validar stock
                        if medicine.stock_quantity < quantity:
                            prescription.delete()
                            messages.error(request, f'❌ Stock insuficiente de {medicine.name}. Stock disponible: {medicine.stock_quantity}')
                            return redirect('doctor-create-prescription')
                            
                    except models.Medicine.DoesNotExist:
                        prescription.delete()
                        messages.error(request, f'❌ Medicamento no encontrado')
                        return redirect('doctor-create-prescription')
                    except ValueError:
                        prescription.delete()
                        messages.error(request, '❌ Cantidad inválida')
                        return redirect('doctor-create-prescription')
            
            # Si pasa la validación, crear los PrescriptionMedicine
            for i in range(len(medicine_ids)):
                if medicine_ids[i] and quantities[i]:
                    medicine = models.Medicine.objects.get(id=medicine_ids[i])
                    quantity = int(quantities[i])
                    
                    # Crear PrescriptionMedicine (esto automáticamente reducirá el stock via el save())
                    prescription_medicine = models.PrescriptionMedicine(
                        prescription=prescription,
                        medicine=medicine,
                        quantity=quantity,
                        dosage=dosages[i] if i < len(dosages) else '',
                        duration=durations[i] if i < len(durations) else ''
                    )
                    prescription_medicine.save()
                    print(f"✅ Medicamento {medicine.name} agregado a receta. Stock reducido en {quantity}")
            
            # ASOCIAR LA RECETA CON LA CITA SI VIENE DE UNA
            if appointment_id:
                try:
                    appointment = models.Appointment.objects.get(id=appointment_id)
                    appointment.prescription = prescription
                    appointment.status = 'done'  # Marcar cita como atendida
                    appointment.save()
                    print(f"✅ Receta {prescription.id} asociada a cita {appointment_id}")
                except models.Appointment.DoesNotExist:
                    print(f"❌ Cita {appointment_id} no encontrada")
            
            messages.success(request, '✅ Receta médica creada exitosamente y stock actualizado')
            return redirect('doctor-view-prescription')  # ← ESTA ES LA LÍNEA IMPORTANTE
            
        except Exception as e:
            print(f"DEBUG: Error general: {str(e)}")
            messages.error(request, f'❌ Error al crear receta: {str(e)}')
            # Si hay algún error, redirigir de nuevo al formulario
            return redirect('doctor-create-prescription')
    
    # Si viene de una cita, preseleccionar el paciente
    initial_data = {}
    if patient_id:
        try:
            patient = models.Patient.objects.get(id=patient_id)
            initial_data['patient'] = patient
        except models.Patient.DoesNotExist:
            pass
    
    return render(request, 'hospital/doctor_create_prescription.html', {
        'doctor': doctor,
        'my_patients': my_patients,
        'medicines': medicines,
        'initial_patient': initial_data.get('patient'),
        'appointment_id': appointment_id
    })

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_prescription_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    
    # Obtener todas las recetas del doctor actual
    prescriptions = models.Prescription.objects.filter(doctor=doctor).order_by('-created_at')
    
    # Contadores para estadísticas
    total_prescriptions = prescriptions.count()
    pending_prescriptions = prescriptions.filter(status='pendiente').count()
    completed_prescriptions = prescriptions.filter(status='completada').count()
    cancelled_prescriptions = prescriptions.filter(status='cancelada').count()
    
    # Aplicar filtros si existen
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        prescriptions = prescriptions.filter(status=status_filter)
    
    return render(request, 'hospital/doctor_view_prescription.html', {
        'prescriptions': prescriptions,
        'doctor': doctor,
        'total_prescriptions': total_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'completed_prescriptions': completed_prescriptions,
        'cancelled_prescriptions': cancelled_prescriptions,
        'current_filter': status_filter
    })
    
    
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_prescription_view(request):
    return render(request, 'hospital/admin_prescription.html')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_prescription_view(request):
    prescriptions = models.Prescription.objects.all().order_by('-created_at')
    
    return render(request, 'hospital/admin_view_prescription.html', {
        'prescriptions': prescriptions
    })

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_process_prescription_view(request, pk):
    prescription = get_object_or_404(models.Prescription, id=pk)
    
    if request.method == 'POST' and prescription.status == 'pendiente':
        try:
            # Procesar cada medicamento en la receta
            for prescription_medicine in prescription.medicines.all():
                medicine = prescription_medicine.medicine
                quantity = prescription_medicine.quantity
                
                # Verificar stock nuevamente antes de procesar
                if medicine.stock_quantity < quantity:
                    messages.error(request, f'Stock insuficiente de {medicine.name}. Stock disponible: {medicine.stock_quantity}')
                    return redirect('admin-view-prescription')
                
                # Restar del inventario
                medicine.stock_quantity -= quantity
                medicine.save()
                
                # Registrar movimiento de salida
                models.MedicineMovement.objects.create(
                    medicine=medicine,
                    movement_type='salida',
                    quantity=quantity,
                    previous_stock=medicine.stock_quantity + quantity,
                    new_stock=medicine.stock_quantity,
                    reason=f'Receta médica #{prescription.id} - {prescription.patient.get_name}',
                    performed_by=request.user
                )
            
            # Marcar receta como completada
            prescription.status = 'completada'
            prescription.save()
            
            messages.success(request, '✅ Receta procesada exitosamente. Stock actualizado.')
            
        except Exception as e:
            messages.error(request, f'❌ Error al procesar receta: {str(e)}')
    
    return redirect('admin-view-prescription')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_prescription_detail_view(request, pk):
    prescription = get_object_or_404(models.Prescription, id=pk)
    
    return render(request, 'hospital/admin_prescription_detail.html', {
        'prescription': prescription
    })
    
    
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_prescription_view(request):
    """Vista para que el paciente vea sus recetas"""
    patient = models.Patient.objects.get(user_id=request.user.id)
    
    # Obtener todas las recetas del paciente
    prescriptions = models.Prescription.objects.filter(patient=patient).order_by('-created_at')
    
    # DEBUG: Verificar qué está pasando con los totales
    print(f"DEBUG: Procesando {prescriptions.count()} recetas para {patient.get_name}")
    
    # Forzar actualización de totales para TODAS las recetas
    for prescription in prescriptions:
        old_total = prescription.total_amount
        new_total = 0
        
        # Calcular manualmente el total
        for medicine_item in prescription.medicines.all():
            if medicine_item.medicine and medicine_item.medicine.price:
                subtotal = float(medicine_item.medicine.price) * medicine_item.quantity
                new_total += subtotal
                print(f"DEBUG: {medicine_item.medicine.name} - {medicine_item.quantity} x ${medicine_item.medicine.price} = ${subtotal}")
        
        # Actualizar si es diferente
        if new_total != float(old_total):
            prescription.total_amount = new_total
            prescription.save()
            print(f"DEBUG: Receta #{prescription.id} actualizada: ${old_total} -> ${new_total}")
        else:
            print(f"DEBUG: Receta #{prescription.id} ya tiene total correcto: ${old_total}")
    
    # Re-cargar las recetas con los totales actualizados
    prescriptions = models.Prescription.objects.filter(patient=patient).order_by('-created_at')
    
    # Calcular totales
    total_prescriptions = prescriptions.count()
    pending_payment = prescriptions.filter(payment_status='pendiente').count()
    paid_prescriptions = prescriptions.filter(payment_status='pagado').count()
    
    # Calcular total pendiente de pago
    total_pendiente = 0
    for prescription in prescriptions.filter(payment_status='pendiente'):
        total_pendiente += float(prescription.total_amount)
    
    return render(request, 'hospital/patient_prescription.html', {
        'patient': patient,
        'prescriptions': prescriptions,
        'total_prescriptions': total_prescriptions,
        'pending_payment': pending_payment,
        'paid_prescriptions': paid_prescriptions,
        'total_pendiente': "{:.2f}".format(total_pendiente)
    })

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_prescription_detail_view(request, pk):
    """Vista detallada de una receta para el paciente"""
    patient = models.Patient.objects.get(user_id=request.user.id)
    prescription = get_object_or_404(models.Prescription, id=pk, patient=patient)
    
    return render(request, 'hospital/patient_prescription_detail.html', {
        'patient': patient,
        'prescription': prescription
    })

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_payment_view(request, pk):
    """Vista para simular el pago de una receta"""
    patient = models.Patient.objects.get(user_id=request.user.id)
    prescription = get_object_or_404(models.Prescription, id=pk, patient=patient)
    
    if request.method == 'POST':
        # Simular procesamiento de pago
        import time
        time.sleep(2)  # Simular delay de procesamiento
        
        # Actualizar estado de pago
        prescription.payment_status = 'pagado'
        prescription.save()
        
        messages.success(request, '✅ Pago procesado exitosamente!')
        return redirect('patient-prescription-detail', pk=pk)
    
    return render(request, 'hospital/patient_payment.html', {
        'patient': patient,
        'prescription': prescription
    })