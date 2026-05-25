from django.urls import path

from . import views

app_name = 'boletos'

urlpatterns = [
    path("", views.BusListView.as_view(), name="bus_list"),
    path("<int:pk>/", views.SeatGridView.as_view(), name="seat_grid"),
    path("asiento/<int:pk>/reservar/", views.SeatReserveView.as_view(), name="reserve"),
    path("mis-reservas/", views.MisReservasView.as_view(), name="mis_reservas"),
    path("asiento/<int:pk>/cancelar/", views.CancelReserveView.as_view(), name="cancel"),
]
