var int;

function x(){
    var c, date, h, t;
    $.ajax({
        url: '/history_dat',
        type : 'POST',
        success: function( data ) {
            c = data['cant'];
            date = data['date'];
            if(c > 0){
                for(var i = 0; i<c; i++){
                    var dat = new Date(date[i]*1000);
                    date[i]=dat.toLocaleString("es-AR");
                }
            }
            console.log(date);
            h = data['hum'];
            t = data['temp'];
            tipo = "Temperature";
            tipo2 = "Humidity";
            grafico(date,t,c,tipo);
            grafico(date,h,c,tipo2);
        }
    });
    clearInterval(int);
}



function tiempo() {
    var selectBox = document.getElementById("seleccion");
    var selectedValue = selectBox.options[selectBox.selectedIndex].value;
    console.log(selectedValue);
    $.post( "/history_sel", { selected: selectedValue});
    startinterval();
}

function startinterval(){
    int = setInterval(x,1000);
}

function grafico(date,data,cant,tipo){
    console.log("pollopa" + cant);
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


