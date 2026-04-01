$(document).ready(function() {
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    $('.sidebar-toggle').on('click', function() {
        $('.sidebar').toggleClass('active');
    });
    
    $('.delete-btn').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
        }
    });
    
    $('table').DataTable({
        "paging": true,
        "ordering": true,
        "searching": true
    });
    
    $('.confirm-action').on('click', function(e) {
        const action = $(this).data('action') || 'perform this action';
        if (!confirm(`Are you sure you want to ${action}?`)) {
            e.preventDefault();
        }
    });
    
    $(document).on('change', '.status-select', function() {
        const appointmentId = $(this).data('id');
        const newStatus = $(this).val();
        
        $.ajax({
            url: `/appointments/${appointmentId}/update-status/`,
            method: 'POST',
            data: {
                status: newStatus,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    showNotification('Status updated successfully', 'success');
                }
            },
            error: function() {
                showNotification('Error updating status', 'error');
            }
        });
    });
    
    function showNotification(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const notification = $(`
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        );
        $('.main-content').prepend(notification);
        setTimeout(() => notification.alert('close'), 5000);
    }
    
    $('.print-btn').on('click', function(e) {
        e.preventDefault();
        window.print();
    });
    
    $(document).on('change', '#id_quantity, #id_unit_price', function() {
        const quantity = parseFloat($('#id_quantity').val()) || 0;
        const unitPrice = parseFloat($('#id_unit_price').val()) || 0;
        const total = quantity * unitPrice;
        $('#calculated_total').text(total.toFixed(2));
    });
});

function updateInvoiceTotal() {
    let subtotal = 0;
    $('.item-row').each(function() {
        const quantity = parseFloat($(this).find('.quantity-input').val()) || 0;
        const price = parseFloat($(this).find('.price-input').val()) || 0;
        subtotal += quantity * price;
    });
    
    const tax = parseFloat($('#id_tax_amount').val()) || 0;
    const discount = parseFloat($('#id_discount_amount').val()) || 0;
    const total = subtotal + tax - discount;
    
    $('#subtotal-display').text(subtotal.toFixed(2));
    $('#total-display').text(total.toFixed(2));
}

$(document).on('change', '.item-row input', updateInvoiceTotal);
