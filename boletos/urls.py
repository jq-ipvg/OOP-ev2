from django.urls import path

from . import views

app_name = 'boletos'

urlpatterns = [
    path("", views.BusListView.as_view(), name="bus_list"),
    path("<int:pk>/", views.SeatGridView.as_view(), name="seat_grid"),
    path("asiento/<int:pk>/reservar/", views.SeatReserveView.as_view(), name="reserve"),
]
