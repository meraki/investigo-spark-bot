function plot(map_source, typeOneCoordinates, typeTwoCoordinates, floorWidth, floorHeight, floorLength, imgWidth, imgHeight) {
	/*
	console.log(map_source);
	console.log(typeOneCoordinates);
	console.log(typeTwoCoordinates);
	console.log("Floor width: " + floorWidth);
	console.log("Floor length: " + floorHeight);
	console.log("Floor length: " + floorLength);
	console.log(imgWidth);
	console.log(imgHeight);
	*/

	var addition = typeOneCoordinates.length + typeTwoCoordinates.length;
	
	console.log("Plotting " + addition + " devices on map");
	
	//console.log(map_source);
	var canvas = document.getElementById('map-canvas');
	if (canvas) {
		var ctx = canvas.getContext('2d');
		// Create an image element
		var imgMapBackground = new Image();

		// Specify the src to load the image
		imgMapBackground.src = map_source;

		//console.log(map_source)
		
		// When the image is loaded, draw it.
			imgMapBackground.onload = function() {
		
			    var imgWidth = imgMapBackground.width;
			    var imgHeight = imgMapBackground.height;

			    var largerDimension = 800;
			    var lowerDimension = 600;

			    var apiProvidedWidth = imgWidth;
			    var apiProvidedHeight = imgHeight;

			    canvas.width = 800;
			    canvas.height = 600;

			    ctx.drawImage(imgMapBackground, 0, 0, imgWidth, imgHeight, 0, 0, canvas.width, canvas.height);
			    if (typeOneCoordinates.length > 0) {
			        plotCoordinatesInArray(canvas, ctx, typeOneCoordinates, true, floorWidth, floorLength);
			    }
			    if (typeTwoCoordinates.length > 0) {
			        plotCoordinatesInArray(canvas, ctx, typeTwoCoordinates, false, floorWidth, floorLength);
			    }
			    
			}
	    }
			
}

function plotCoordinatesInArray(canvas, ctx, array, typeOne, floorWidth, floorLength) {
    //console.log('plot coordinates in array: ' + array.toString())
	for (var i = 0; i < array.length; i++){
    	coordinate = array[i];
    	var mapCoordinateX = coordinate[0];
        var mapCoordinateY = coordinate[1];

        /*
        console.log("Coordinate X: " + mapCoordinateX);
        console.log("Coordinate Y: " + mapCoordinateY);
        console.log("Canvas width: " + canvas.width);
        console.log("Canvas height: " + canvas.height);
        */
        console.log("Floor width: " + floorWidth);

        var posXtoPlot = Math.floor(mapCoordinateX * canvas.width / floorWidth);
    	var posYtoPlot = Math.floor(mapCoordinateY * canvas.height / floorLength);
    	//console.log("Will plot marker on: (" + posXtoPlot + ", " + posYtoPlot + ")");
    	
    	var outsideCanvas = false;
    	
    	if (posXtoPlot > canvas.width) {
    		posXtoPlot = canvas.width
    		outsideCanvas = true;
    	}
    	
    	if (posYtoPlot > canvas.height) {
    		posYtoPlot = canvas.height
    		outsideCanvas = true;
    	}
    	
    	plotOnCanvas(ctx, posXtoPlot, posYtoPlot, typeOne);
    }
} 

function plotOnCanvas(ctx, posXtoPlot, posYtoPlot, typeOne) {
	//TODO Check for negative numbers
	console.log('plot on canvas: ' + posXtoPlot + " " + posYtoPlot)
	var radius = 10;
	var lineWidth = radius/3
	ctx.beginPath();
	ctx.arc(posXtoPlot, posYtoPlot, radius, 0, 2 * Math.PI, false);
	ctx.fill();
	ctx.lineWidth = lineWidth;
	
	
	var color = 'blue'
	var strokeStyle = 'yellow'	
	if (!typeOne){
		color = 'red'
		strokeStyle = 'green'
	} 
	ctx.fillStyle = color;
	ctx.strokeStyle = strokeStyle;		
	
	ctx.stroke();
}
//query should be configured relative to the size of the image uploaded for the map.
//So in this example, the image is 1000x500 pixels and the dimensions of the floor are 200ftx100ft 
//so the if an access point or client device is reporting being at location x=70, y = 70, in the image the device would be located at pixel 350x350.
