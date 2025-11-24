from django.db import models
from django.contrib.auth.models import User


departments=[ 
    ('Cardiólogo', 'Cardiólogo'),
    ('Dermatólogo', 'Dermatólogo'),
    ('Especialista en Medicina de Emergencias', 'Especialista en Medicina de Emergencias'),
    ('Alergólogo/Inmunólogo', 'Alergólogo/Inmunólogo'),
    ('Anestesiólogo', 'Anestesiólogo'),
    ('Cirujano Colorrectal', 'Cirujano Colorrectal'),
]
class Doctor(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/DoctorProfilePic/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    department= models.CharField(max_length=50,choices=departments,default='Cardiologist')
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return "{} ({})".format(self.user.first_name,self.department)



class Patient(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/PatientProfilePic/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    symptoms = models.CharField(max_length=100,null=False)
    assignedDoctorId = models.PositiveIntegerField(null=True)
    admitDate=models.DateField(auto_now=True)
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return self.user.first_name+" ("+self.symptoms+")"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En espera'),
        ('done', 'Atendido'),
        ('cancelled', 'Cancelado'),
    ]

    patientId = models.PositiveIntegerField(null=True)
    doctorId = models.PositiveIntegerField(null=True)
    patientName = models.CharField(max_length=40, null=True)
    doctorName = models.CharField(max_length=40, null=True)
    appointmentDate = models.DateField(auto_now=True)
    description = models.TextField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    prescription = models.ForeignKey('Prescription', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Receta asociada")




class PatientDischargeDetails(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40)
    assignedDoctorName=models.CharField(max_length=40)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    symptoms = models.CharField(max_length=100,null=True)

    admitDate=models.DateField(null=False)
    releaseDate=models.DateField(null=False)
    daySpent=models.PositiveIntegerField(null=False)

    roomCharge=models.PositiveIntegerField(null=False)
    medicineCost=models.PositiveIntegerField(null=False)
    doctorFee=models.PositiveIntegerField(null=False)
    OtherCharge=models.PositiveIntegerField(null=False)
    total=models.PositiveIntegerField(null=False)


class MedicineCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Medicine(models.Model):
    UNIT_CHOICES = [
        ('tabletas', 'Tabletas'),
        ('capsulas', 'Cápsulas'),
        ('ml', 'Mililitros (ml)'),
        ('mg', 'Miligramos (mg)'),
        ('g', 'Gramos (g)'),
        ('unidades', 'Unidades'),
        ('frascos', 'Frascos'),
        ('ampollas', 'Ampollas'),
        ('jeringas', 'Jeringas'),
    ]
    
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='tabletas')
    stock_quantity = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=10)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    supplier = models.CharField(max_length=200, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    requires_prescription = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.stock_quantity} {self.unit}"
    
    @property
    def stock_status(self):
        if self.stock_quantity <= 0:
            return 'agotado'
        elif self.stock_quantity <= self.min_stock:
            return 'bajo'
        else:
            return 'normal'
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

class MedicineMovement(models.Model):
    MOVEMENT_TYPES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reason = models.CharField(max_length=200)
    movement_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Solo para nuevos registros
            if self.movement_type == 'entrada':
                self.medicine.stock_quantity += self.quantity
            elif self.movement_type == 'salida':
                self.medicine.stock_quantity -= self.quantity
            self.medicine.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.movement_type} - {self.medicine.name} - {self.quantity}"
    
class Prescription(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pendiente', 'Pendiente de Pago'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Paciente")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Doctor")
    diagnosis = models.TextField(verbose_name="Diagnóstico")
    symptoms = models.TextField(verbose_name="Síntomas")
    instructions = models.TextField(verbose_name="Instrucciones para el paciente")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pendiente')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Monto Total")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Receta #{self.id} - {self.patient.get_name} - {self.doctor.get_name}"
    
    def calculate_total(self):
        """Calcular el total sumando todos los medicamentos"""
        total = 0
        for medicine_item in self.medicines.all():
            if medicine_item.medicine and medicine_item.medicine.price:
                total += float(medicine_item.medicine.price) * medicine_item.quantity
        return total
    
    def save(self, *args, **kwargs):
        # Calcular el total automáticamente al guardar, incluso para nuevos registros
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Guardar primero para tener ID
        
        # Si ya tiene medicamentos, calcular el total
        if self.medicines.exists():
            self.total_amount = self.calculate_total()
            # Llamar super().save() otra vez para guardar el total
            super().save(update_fields=['total_amount'])
    
    class Meta:
        verbose_name = "Receta Médica"
        verbose_name_plural = "Recetas Médicas"

class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='medicines')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, verbose_name="Medicamento")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    dosage = models.CharField(max_length=200, verbose_name="Dosis", help_text="Ej: 1 tableta cada 8 horas")
    duration = models.CharField(max_length=100, verbose_name="Duración", help_text="Ej: 7 días")
    
    @property
    def subtotal(self):
        """Calcular subtotal por medicamento"""
        return float(self.medicine.price) * self.quantity
    
    def save(self, *args, **kwargs):
        # Reducir el stock solo si es un nuevo registro
        if self.pk is None:
            if self.medicine.stock_quantity >= self.quantity:
                # Guardar el stock anterior
                previous_stock = self.medicine.stock_quantity
                
                # Reducir el stock
                self.medicine.stock_quantity -= self.quantity
                self.medicine.save()
                
                # Registrar el movimiento de salida
                MedicineMovement.objects.create(
                    medicine=self.medicine,
                    movement_type='salida',
                    quantity=self.quantity,
                    previous_stock=previous_stock,
                    new_stock=self.medicine.stock_quantity,
                    reason=f'Receta #{self.prescription.id} - {self.prescription.patient.get_name}',
                    performed_by=self.prescription.doctor.user
                )
                
                # Actualizar el total de la receta
                self.prescription.save()
            else:
                raise ValueError(f"Stock insuficiente para {self.medicine.name}. Stock disponible: {self.medicine.stock_quantity}")
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Restaurar el stock al eliminar
        previous_stock = self.medicine.stock_quantity
        self.medicine.stock_quantity += self.quantity
        self.medicine.save()
        
        # Registrar movimiento de ajuste por eliminación
        MedicineMovement.objects.create(
            medicine=self.medicine,
            movement_type='ajuste',
            quantity=self.quantity,
            previous_stock=previous_stock,
            new_stock=self.medicine.stock_quantity,
            reason=f'Receta #{self.prescription.id} eliminada - Stock restaurado',
            performed_by=self.prescription.doctor.user
        )
        
        # Actualizar el total de la receta
        self.prescription.save()
        
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.quantity} unidades"
    
    class Meta:
        verbose_name = "Medicamento en Receta"
        verbose_name_plural = "Medicamentos en Recetas"
        
        
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Prescription)
def update_appointment_prescription(sender, instance, created, **kwargs):
    """
    Actualizar la cita con la receta asociada automáticamente
    """
    if created:
        try:
            # Buscar la cita pendiente relacionada con este paciente y doctor
            appointment = models.Appointment.objects.filter(
                patientId=instance.patient.id,
                doctorId=instance.doctor.id,
                status='pending'
            ).first()
            
            if appointment:
                appointment.prescription = instance
                appointment.status = 'done'  # Marcar como atendido
                appointment.save()
                print(f"✅ Cita {appointment.id} actualizada con receta {instance.id}")
        except Exception as e:
            print(f"❌ Error al asociar cita con receta: {e}")
            
            
            
def update_all_prescription_totals():
    """Función temporal para actualizar todos los totales"""
    from hospital.models import Prescription
    prescriptions = Prescription.objects.all()
    
    for prescription in prescriptions:
        total = 0
        print(f"Receta #{prescription.id}:")
        
        for medicine_item in prescription.medicines.all():
            if medicine_item.medicine and medicine_item.medicine.price:
                subtotal = float(medicine_item.medicine.price) * medicine_item.quantity
                total += subtotal
                print(f"  - {medicine_item.medicine.name}: {medicine_item.quantity} x ${medicine_item.medicine.price} = ${subtotal}")
        
        if total != float(prescription.total_amount):
            prescription.total_amount = total
            prescription.save()
            print(f"  TOTAL ACTUALIZADO: ${prescription.total_amount}")
        else:
            print(f"  TOTAL CORRECTO: ${prescription.total_amount}")
        print("---")
        
        # Ejecutar esto una vez (luego comentar o eliminar)
if __name__ == "__main__":
    update_all_prescription_totals()