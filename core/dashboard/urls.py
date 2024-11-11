from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'modules', views.ModuleViewSet)
router.register(r'iolists', views.IOListViewSet)
router.register(r'signals', views.SignalsViewSet)
router.register(r'projectreports', views.ProjectReportViewSet)

urlpatterns = [
#dashboard 
    path('', views.home, name = 'dash-home'),
    path('api/', include(router.urls)),
]


"""
  <div id="container" style="width: 75%;">
    <canvas id="population-chart" data-url="{% url 'dash-home' %}"></canvas>
  </div>

  <script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.3/dist/Chart.min.js"></script>
  <script>

    $(function () {

      var $populationChart = $("#dash-home");
      $.ajax({
        url: $populationChart.data("url"),
        success: function (data) {

          var ctx = $populationChart[0].getContext("2d");

          new Chart(ctx, {
            type: 'bar',
            data: {
              labels: data.labels,
              datasets: [{
                label: 'Population',
                backgroundColor: 'blue',
                data: data.data
              }]          
            },
            options: {
              responsive: true,
              legend: {
                position: 'top',
              },
              title: {
                display: true,
                text: 'Population Bar Chart'
              }
            }
          });

        }
      });

    });

  </script>

{% endblock %}"""