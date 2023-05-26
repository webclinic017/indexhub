import React, { useContext, useEffect, useRef, useState } from 'react';
import { Point3D, Dataset, ScatterGL, ScatterGLParams, PointMetadata, RenderMode } from 'scatter-gl';  // adjust these imports based on your project structure
import { Stack, VStack, Button, Box } from '@chakra-ui/react';
import { useTrendsContext } from './trends_context';

export interface ProjectorData {
    ids: number[];
    clusters: number[];
    entityIds: string[];   // entity names
    projections: Point3D[];
}

const getProjectorData = async (datasetId: string, apiToken: string) => {
    console.log(`api call token = ${apiToken}`);
    const response = await fetch(
        `${process.env.REACT_APP__FASTAPI__DOMAIN}/trends/public/vectors/${datasetId}`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${apiToken}`,
            },
            body: JSON.stringify({ "dim_size": 3 }),
        }
    );
    const response_json = await response.json();
    return response_json;
};

const enum CanvasState {
    IDLE = 0,
    PAN = 1,
    HOVER = 2,
    CLICK = 3,
}
const ORBIT_DELAY = 3000;

const Projector = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const messagesRef = useRef<HTMLDivElement>(null);
    const scatterGLRef = useRef<ScatterGL | null>(null);
    const [dataset, setDataset] = useState<Dataset | null>(null);
    const [canvasState, setCanvasState] = useState<CanvasState>(CanvasState.IDLE);
    const {
        selectPoint,
        // addPoint,
        // resetPoints,
        projectorData,
        updateProjectorData,
        apiToken,
        datasetId
    } = useTrendsContext();

    const getDatasetFromProjectorData = (data: ProjectorData) => {
        const newPoints: Point3D[] = [];
        const metadata: PointMetadata[] = [];
        data.projections.forEach((vector, index) => {
            newPoints.push(vector);
            metadata.push({
                id: data.ids[index],
                label: data.entityIds[index],
                cluster: data.clusters[index],
            });
        });

        const dataset = new Dataset(newPoints, metadata);
        return dataset;
    }

    // Only rerender when dataset changes
    useEffect(() => {
        if (!dataset || !scatterGLRef.current) {
            return;
        }
        scatterGLRef.current.render(dataset);
    }, [dataset])

    // When projectorData changes, update the projector
    useEffect(() => {
        if (!scatterGLRef.current || !projectorData) {
            return;
        }
        const dataset = getDatasetFromProjectorData(projectorData);
        setDataset(dataset);

    }, [projectorData]);

    // When datasetId changes, update the projector data
    useEffect(() => {
        const getAsync = async () => {
            const data = await getProjectorData(datasetId, apiToken) as ProjectorData;
            // resetPoints();
            updateProjectorData(data);
        }
        if (datasetId && apiToken) {
            getAsync();
        }
    }, [datasetId, apiToken]);

    useEffect(() => {
        if (!scatterGLRef.current) {
            return;
        }
        console.log(`canvasState = ${canvasState}`);
        if (canvasState === CanvasState.IDLE) {
            const timer = setTimeout(() => {
                scatterGLRef.current?.startOrbitAnimation();
            }, ORBIT_DELAY);
            return () => clearTimeout(timer);
        } else {
            scatterGLRef.current.stopOrbitAnimation();
        }
    }, [canvasState]);

    // Initialize the canvas
    useEffect(() => {
        const setupAsync = async () => {
            if (!containerRef.current || scatterGLRef.current) {
                return;
            }
            console.log(`Start projector mount`);

            const setMessage = (message: string) => {
                const messageStr = `🔥 ${message}`;
                console.log(messageStr);
                if (messagesRef.current) {
                    messagesRef.current.innerHTML = messageStr;
                }
            };
            const renderMode = "POINT" as RenderMode.POINT;
            const params: ScatterGLParams = {
                onClick: (pointIndex: number | null) => {
                    setMessage(`click ${pointIndex}`);
                    if (pointIndex !== null) {
                        selectPointHandler(pointIndex);
                    }
                    setCanvasState(pointIndex === null ? CanvasState.IDLE : CanvasState.CLICK);
                },
                onHover: (point: number | null) => {
                    setMessage(`hover ${point}`);
                    setCanvasState(point === null ? CanvasState.IDLE : CanvasState.HOVER);
                },
                onCameraMove: (value) => {
                    setMessage(`camera move: ${JSON.stringify(value)}`);
                    setCanvasState(CanvasState.PAN);
                },
                renderMode: renderMode,
                orbitControls: {
                    zoomSpeed: 1.125,
                },
            };
            scatterGLRef.current = new ScatterGL(containerRef.current, params);
            
            // Add in a resize observer for automatic window resize.
            // const resizeFunc = () => scatterGLRef.current?.resize();
            // window.addEventListener('resize', resizeFunc);

            // const handleInputChange: EventListener = (event) => {
            //     const inputElement = event.target as HTMLInputElement;
            //     console.log(`inputElement.value = ${inputElement.value}`)
            //     if (inputElement.value === 'pan') {
            //         scatterGLRef.current?.setPanMode();
            //     } else if (inputElement.value === 'select') {
            //         scatterGLRef.current?.setSelectMode();
            //     }
            // };

            // const inputElements = containerRef.current?.querySelectorAll<HTMLInputElement>(
            //     'input[name="interactions"]'
            // );

            // inputElements?.forEach((inputElement) => {
            //     inputElement.addEventListener('change', handleInputChange);
            // });

            console.log(`End projector mount`);

            // Clean up function for removing the resize listener when the component unmounts
            // return () => {
            //     window.removeEventListener('resize', resizeFunc);
            // inputElements?.forEach((inputElement) => {
            //     inputElement.removeEventListener('change', handleInputChange);
            // });
            // }
        }
        setupAsync();
    }, []);

    // Your button and input handlers go here...
    const selectPointHandler = (id: number) => {
        console.log(`selectPointHandler ${id} of type ${typeof id}`);
        selectPoint(id);
        // addPoint(id);
    };

    const selectRandomHandler = () => {
        if (!dataset) {
            return;
        }
        if (scatterGLRef.current && dataset.points.length > 0) {
            const randomIndex = Math.floor(dataset.points.length * Math.random());
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
                    <div ref={messagesRef} />
                </Stack>
            </VStack>
        </Box>
    );
}

export default Projector;
