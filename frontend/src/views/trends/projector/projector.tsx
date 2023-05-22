import React, { useContext, useEffect, useRef, useState } from 'react';
import { Point3D, Dataset, ScatterGL, ScatterGLParams, PointMetadata } from 'scatter-gl';  // adjust these imports based on your project structure
import { data } from './data/projection';  // adjust this import based on your project structure
import { Stack, VStack, Button, Box } from '@chakra-ui/react';
import { TrendsContext } from '../trends';

const Projector = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const messagesRef = useRef<HTMLDivElement>(null);
    const scatterGLRef = useRef<ScatterGL | null>(null);
    const [dataPoints, setDataPoints] = useState<Point3D[]>([]);
    const [metadata, setMetadata] = useState<PointMetadata[]>([]);  // All points
    const { selectedPoints, addPoint } = useContext(TrendsContext);

    useEffect(() => {
        console.log(`selectedPoints in projector: ${selectedPoints.map(item => item.pointIndex as number)}`);
    }, [selectedPoints]);


    useEffect(() => {
        if (containerRef.current) {
            // Construct dataset
            const newPoints: Point3D[] = [];
            const metadata: PointMetadata[] = [];
            data.projection.forEach((vector, index) => {
                const labelIndex = data.labels[index];
                newPoints.push(vector);
                metadata.push({
                    labelIndex,
                    label: data.labelNames[labelIndex],
                    pointIndex: index,
                });
            });

            setDataPoints(newPoints);
            setMetadata(metadata);
            const dataset = new Dataset(newPoints, metadata);  // Define the dataset here

            const setMessage = (message: string) => {
                const messageStr = `🔥 ${message}`;
                console.log(messageStr);
                if (messagesRef.current) {
                    messagesRef.current.innerHTML = messageStr;
                }
            };

            const params: ScatterGLParams = {
                onClick: (pointIndex: number | null) => {
                    setMessage(`click ${pointIndex}`);
                    if (pointIndex !== null) {
                        const labelIndex = data.labels[pointIndex];
                        const currPoint: PointMetadata = {
                            labelIndex,
                            label: data.labelNames[labelIndex],
                            pointIndex: pointIndex,
                        }
                        addPoint(currPoint);
                    }
                },
                onHover: (point: number | null) => {
                    setMessage(`hover ${point}`);
                },
                // renderMode: RenderMode.POINT,
                orbitControls: {
                    zoomSpeed: 1.125,
                },
            };
            scatterGLRef.current = new ScatterGL(containerRef.current, params);

            scatterGLRef.current.render(dataset);

            // Add in a resize observer for automatic window resize.
            const resizeFunc = () => scatterGLRef.current?.resize();
            window.addEventListener('resize', resizeFunc);

            const handleInputChange: EventListener = (event) => {
                const inputElement = event.target as HTMLInputElement;
                if (inputElement.value === 'pan') {
                    scatterGLRef.current?.setPanMode();
                } else if (inputElement.value === 'select') {
                    scatterGLRef.current?.setSelectMode();
                }
            };

            const inputElements = containerRef.current?.querySelectorAll<HTMLInputElement>(
                'input[name="interactions"]'
            );

            inputElements?.forEach((inputElement) => {
                inputElement.addEventListener('change', handleInputChange);
            });


            // Clean up function for removing the resize listener when the component unmounts
            return () => {
                window.removeEventListener('resize', resizeFunc);
                inputElements?.forEach((inputElement) => {
                    inputElement.removeEventListener('change', handleInputChange);
                });
            }
        }
    }, []);  // Empty array means this effect runs once on mount and clean up on unmount

    // Your button and input handlers go here...
    const selectRandomHandler = () => {
        if (scatterGLRef.current && dataPoints.length > 0) {
            const randomIndex = Math.floor(dataPoints.length * Math.random());
            scatterGLRef.current.select([randomIndex]);
        }
    };

    const toggleOrbitHandler = () => {
        if (scatterGLRef.current) {
            if (scatterGLRef.current.isOrbiting()) {
                scatterGLRef.current.stopOrbitAnimation();
            } else {
                scatterGLRef.current.startOrbitAnimation();
            }
        }
    };

    return (
        <Box id="trends-projector" height="100%" width="100%">
            <VStack style={{ flex: 1, width: '100%', height: '100%' }}>
                <div id="this_is_the_container" ref={containerRef} style={{ flex: 1, width: '100%', height: '100vh' }} />
                <Stack direction={{ base: 'column', md: 'row' }}>
                    <Button
                        rounded={'full'}
                        bg={'blue.400'}
                        color={'white'}
                        _hover={{
                            bg: 'blue.500',
                        }}
                        onClick={toggleOrbitHandler}>
                        Toggle Orbit
                    </Button>
                    <Button rounded={'full'} onClick={selectRandomHandler}>Select Random</Button>
                    <div id="messages" ref={messagesRef} style={{ flex: 1 }} />
                </Stack>
            </VStack>
        </Box>
    );
}

export default Projector;
