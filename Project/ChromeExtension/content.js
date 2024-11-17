const videoElement = document.querySelector('video'); // Get the YouTube video element
console.log("SUCCESS!")
if (videoElement) {
    // Create a canvas to extract video frames
    const videoCanvas = document.createElement('canvas');
    const videoCtx = videoCanvas.getContext('2d', { willReadFrequently: true });

    // Create a separate canvas for drawing the bounding boxes
    const overlayCanvas = document.createElement('canvas');
    const overlayCtx = overlayCanvas.getContext('2d');
    overlayCanvas.style.position = 'absolute';
    overlayCanvas.style.pointerEvents = 'none';
    overlayCanvas.style.zIndex = '1000';
    document.body.appendChild(overlayCanvas);

    const updateCanvasSize = () => {
        const videoRect = videoElement.getBoundingClientRect();
        videoCanvas.width = videoElement.videoWidth;
        videoCanvas.height = videoElement.videoHeight;
        overlayCanvas.width = videoRect.width;
        overlayCanvas.height = videoRect.height;
        overlayCanvas.style.left = `${videoRect.left}px`;
        overlayCanvas.style.top = `${videoRect.top}px`;
    };

    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);

    // Function to extract video frames and send to the Python API
    const processFrame = async () => {

        if (!videoElement || videoElement.paused || videoElement.ended) {
            return; // Exit if no video is found or the video is not playing
        }
    
        if (videoElement.videoWidth === 0 || videoElement.videoHeight === 0) {
            console.warn('Video dimensions are not yet available.');
            return; // Exit if video dimensions are not available (e.g., the video is still loading)
        }

        videoCtx.drawImage(videoElement, 0, 0, videoCanvas.width, videoCanvas.height);

        // Convert the video frame to a base64-encoded image
        const frameData = videoCanvas.toDataURL('image/jpeg', 0.5);

        try {
            const startTime = performance.now();
            // Send the frame to the Python API
            const response = await fetch('http://localhost:5000/getboxes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: frameData.split(',')[1],  // Send only the base64 string (without "data:image/jpeg;base64,")
                  }),
            });

            const result = await response.json();

            const totalEndTime = performance.now();

            console.log('Total time taken:', (totalEndTime - startTime).toFixed(2), 'ms');

            // Render the bounding boxes on the overlay canvas
            renderBoundingBoxes(result.processed_boxes);
//            console.log("START");
//            console.log(result);
//            console.log(result.processed_boxes);
//            console.log(result.processed_boxes[0]);
 //           console.log(result.processed_boxes.boxesData);
        } catch (error) {
            console.error('Error sending frame to API:', error);
        }
    };

    // Function to render bounding boxes
    const renderBoundingBoxes = (boxes) => {
//        console.log(boxes[0])
//        console.log("WE ARE GONNA DRAW SHIT");
//        console.log(boxes)
//        console.log("WE STILL DRAWING 0");
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height); // Clear the canvas
        overlayCtx.strokeStyle = 'red';
        overlayCtx.lineWidth = 2;
        overlayCtx.font = '14px Arial';
        overlayCtx.fillStyle = 'red';
        if (!boxes) {
            return
        }
//        console.log("WE STILL DRAWING");
        boxes.forEach((box) => {
//            console.log("HUHHH");
//           console.log(box.x);
//            console.log(box.y);
            // Scale bounding boxes to match the overlay canvas size
            const scaleX = overlayCanvas.width / videoCanvas.width;
            const scaleY = overlayCanvas.height / videoCanvas.height;

            const x = box.x * scaleX;
            const y = box.y * scaleY;
            const width = box.width * scaleX;
            const height = box.height * scaleY;

            // Draw rectangle
            overlayCtx.strokeRect(x, y, width, height);

            // Draw label
            overlayCtx.fillText(box.label, x, y - 5);

//            console.log("BLUR TIME");
//            const frameData = videoCtx.getImageData(x, y, width, height);

            //This function works but is too delayed + ca[tures wrong area to blur?
            //blurBox(x, y, width, height);


            /*
            // Create an offscreen canvas to blur the region
            const offscreenCanvas = document.createElement('canvas');
            offscreenCanvas.width = width;
            offscreenCanvas.height = height;
            const offscreenCtx = offscreenCanvas.getContext('2d');
            offscreenCtx.putImageData(frameData, 0, 0);

            // Apply CSS blur effect
            offscreenCtx.filter = 'blur(100px)';
            offscreenCtx.drawImage(offscreenCanvas, 0, 0);
            */
        });
    };
    function blurBox(x, y, width, height) {
        // Step 1: Draw semi-transparent "blur mask" over the bounding box
        overlayCtx.fillStyle = 'rgba(255, 255, 255, 0.6)';  // Semi-transparent white
        overlayCtx.fillRect(x, y, width, height);
    
        // Step 2: Re-render the video frame content (this is what gives the blur effect)
        overlayCtx.globalCompositeOperation = 'source-atop';
        overlayCtx.drawImage(videoCanvas, 0, 0);
        overlayCtx.globalCompositeOperation = 'source-over';  // Reset the composite operation
    }

    // Process frames at a specific interval (e.g., 10 FPS)
    setInterval(processFrame, 100);
} else {
    console.error('Video element not found!');
}

/*
// content.js
console.log("Content script loaded!")
// Function to capture the video frame and send it to the Python server for processing
async function processAndOverlayFrame() {
    console.log("Content Time")
    const video = document.querySelector('video');
    if (!video || video.paused || video.ended) {
        return; // Exit if no video is found or the video is not playing
    }

    if (video.videoWidth === 0 || video.videoHeight === 0) {
        console.warn('Video dimensions are not yet available.');
        return; // Exit if video dimensions are not available (e.g., the video is still loading)
    }
  
    // Create a canvas to capture the current video frame
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  
    // Draw the video frame onto the canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
    // Convert the canvas image to base64
    const imageData = canvas.toDataURL('image/jpeg');
  
    // Send the image data to the Python backend for processing
    const response = await fetch('http://localhost:5000/process-frame', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image: imageData.split(',')[1],  // Send only the base64 string (without "data:image/jpeg;base64,")
      }),
    });
  
    const result = await response.json();
    const processedImageBase64 = result.processed_image;
  
    // Create an image element to overlay the processed frame
    const processedImage = new Image();
    processedImage.src = 'data:image/jpeg;base64,' + processedImageBase64;
    processedImage.style.position = 'absolute';
    processedImage.style.pointerEvents = 'none'; // Prevent the overlay from blocking interactions
    processedImage.style.zIndex = '1000';  // Ensure the overlay is on top of the video
    
    const videoRect = video.getBoundingClientRect(); // Get video position and size
    processedImage.style.width = `${videoRect.width}px`;
    processedImage.style.height = `${videoRect.height}px`;
    processedImage.style.left = `${videoRect.left}px`;
    processedImage.style.top = `${videoRect.top}px`;

    // Append the processed image as an overlay on the page
    document.body.appendChild(processedImage);
  }
  
  // Set an interval to continuously process and overlay the frames (you can adjust this interval)
  setInterval(processAndOverlayFrame, 16);
  */