from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('payslip/generate/', views.payslip_generate, name='payslip_generate'),
    path('payslip/generate/bulk/', views.payslip_bulk_generate, name='payslip_bulk_generate'),
    path('payslip/approvals/', views.payslip_approve_list, name='payslip_approve_list'),
    path('payslip/<int:payslip_id>/approve/', views.payslip_approve, name='payslip_approve'),
    path('payslip/<int:payslip_id>/reject/', views.payslip_reject, name='payslip_reject'),
    path('payslip/<int:payslip_id>/revert/', views.payslip_revert_to_pending, name='payslip_revert_to_pending'),
    path('payslip/<int:payslip_id>/delete/', views.payslip_delete, name='payslip_delete'),
    path('payslip/bulk-approve/', views.payslip_bulk_approve, name='payslip_bulk_approve'),
    path('payslip/<int:payslip_id>/', views.payslip_view, name='payslip_view'),
    path('payslip/<int:payslip_id>/preview/', views.payslip_preview_pdf, name='payslip_preview_pdf'),
    path('payslip/<int:payslip_id>/download/', views.payslip_download_pdf, name='payslip_download_pdf'),
    path('payslip/<int:payslip_id>/edit/', views.payslip_edit, name='payslip_edit'),
    path('settings/', views.system_settings, name='system_settings'),
]
