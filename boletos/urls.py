from django.urls import path

from . import views

app_name = 'boletos'

urlpatterns = [
    path("", views.BusListView.as_view(), name="bus_list"),
    path("<int:pk>/", views.SeatGridView.as_view(), name="seat_grid"),
    path("asiento/<int:pk>/reservar/", views.SeatReserveView.as_view(), name="reserve"),
    path("confirmacion/<uuid:pk>/", views.ReservaConfirmadaView.as_view(), name="reserva_confirmada"),
    path("mis-reservas/", views.MisReservasView.as_view(), name="mis_reservas"),
    path("mis-compras/", views.MisComprasView.as_view(), name="mis_compras"),
    path("asiento/<int:pk>/cancelar/", views.CancelReserveView.as_view(), name="cancel"),
    path("pagar/", views.PagarView.as_view(), name="pagar"),
    path("itinerario/<int:pk>/asientos/", views.ItinerarioSeatGridView.as_view(), name="itinerario_seat_grid"),
    path("empresa/", views.CompanyDashboardView.as_view(), name="empresa_dashboard"),
    path("empresa/buses/", views.CompanyBusListView.as_view(), name="empresa_bus_list"),
    path("empresa/buses/crear/", views.CompanyBusCreateView.as_view(), name="empresa_bus_create"),
    path("empresa/buses/<int:pk>/", views.CompanyBusDetailView.as_view(), name="empresa_bus_detail"),
    path("empresa/buses/<int:pk>/editar/", views.CompanyBusUpdateView.as_view(), name="empresa_bus_update"),
    path("empresa/buses/<int:pk>/eliminar/", views.CompanyBusDeleteView.as_view(), name="empresa_bus_delete"),
    path("empresa/rutas/", views.CompanyRutaListView.as_view(), name="empresa_ruta_list"),
    path("empresa/rutas/crear/", views.CompanyRutaCreateView.as_view(), name="empresa_ruta_create"),
    path("empresa/itinerarios/", views.CompanyItinerarioListView.as_view(), name="empresa_itinerario_list"),
    path("empresa/itinerarios/crear/", views.CompanyItinerarioCreateView.as_view(), name="empresa_itinerario_create"),
]
