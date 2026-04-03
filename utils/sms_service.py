def send_sms(phone, message):
    """
    Send SMS to patient.
    Currently just logs - integrate with Twilio/WhatsApp API for production.
    """
    print(f"[SMS] To {phone}: {message}")
    return True


def send_appointment_reminder(appointment):
    """Send appointment reminder to patient"""
    patient = appointment.patient
    if patient.phone:
        message = f"Reminder: Your appointment is scheduled for {appointment.date} at {appointment.time}. Please arrive 10 minutes early."
        send_sms(patient.phone, message)
    return True


def send_invoice_reminder(invoice):
    """Send payment reminder for outstanding invoice"""
    patient = invoice.patient
    if patient.phone:
        message = f"Reminder: Invoice #{invoice.invoice_number} for ${invoice.total_amount} is {invoice.status}. Please settle your payment."
        send_sms(patient.phone, message)
    return True


def send_treatment_summary(patient, treatments):
    """Send treatment summary after visit"""
    if patient.phone:
        treatment_names = ", ".join([t.procedure for t in treatments[:3]])
        message = f"Thank you for visiting! Your treatments: {treatment_names}. Total: ${sum(t.cost for t in treatments)}"
        send_sms(patient.phone, message)
    return True
