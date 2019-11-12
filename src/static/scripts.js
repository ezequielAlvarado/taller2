
function tiempo() {
    var selectBox = document.getElementById("seleccion");
    var selectedValue = selectBox.options[selectBox.selectedIndex].value;
    console.log(selectedValue);
    const socket = io();
    socket.emit('intervalo', inter = selectedValue);
}



function grafico(date,data,cant,tipo){
    console.log(cant);
    if(cant != 0){
        if(tipo == "Temperature"){
            Max = 60;
            Min = 0;
            Step = 5;
            var ctxL = document.getElementById("myChart1").getContext('2d');
            var datos = {
                labels: date,
                datasets: [{
                    label: "Temperature",
                    data: data,
                    backgroundColor: [
                        'rgba(228, 10, 14, .2)',
                    ],
                    borderColor: [
                        'rgba(228, 10, 14, .7)',
                    ],
                    borderWidth: 3
                    }
                ]
            };
        }
        if(tipo == "Humidity"){
            Max = 100;
            Min = 0;
            Step = 10;
            var ctxL = document.getElementById("myChart2").getContext('2d');
            var datos = {
                labels: date,
                datasets: [
                    {
                    label: "Humidity",
                    data: data,
                    backgroundColor: [
                        'rgba(10, 119, 228, .1)',
                    ],
                    borderColor: [
                        'rgba(10, 119, 228, .7)',
                    ],
                    borderWidth: 3
                    }
                ]
            }
        }
        for(var i = 0; i<cant; i++){
            var dat = new Date(date[i]*1000);
            date[i]=dat.toLocaleString("es-AR");
        }
        var chartopt = {
            scales: {
                yAxes: [{
                    ticks: {
                        max: Max,
                        min: Min,
                        stepSize: Step
                    }
                }]
            }
        };
        var myLineChart = new Chart(ctxL, {
            type: 'line',
            data: datos,
            options: chartopt            
        });
    }    
    else{
        document.getElementById("graf1").innerHTML= '<h1> No existen mediciones recientes de temperatura </h1>';
        document.getElementById("graf2").innerHTML= '<h1> No existen mediciones recientes de humedad </h1>';
    }        
}
