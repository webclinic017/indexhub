import React, { useContext, useEffect, useRef, useState } from 'react';
import { Point3D, Dataset, ScatterGL, ScatterGLParams, PointMetadata } from 'scatter-gl';  // adjust these imports based on your project structure
import { Stack, VStack, Button, Box } from '@chakra-ui/react';
import { TrendsContext } from '../trends_dashboard';

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
    console.log(`getProjectorData response_json type=${typeof response_json} value=${JSON.stringify(response_json)}`);
    return response_json;
};


const Projector = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const messagesRef = useRef<HTMLDivElement>(null);
    const scatterGLRef = useRef<ScatterGL | null>(null);
    const [dataset, setDataset] = useState<Dataset>({} as Dataset);
    const {
        addPoint,
        resetPoints,
        projectorData,
        updateProjectorData,
        apiToken,
        datasetId
    } = useContext(TrendsContext);

    // useEffect(() => {
    //     console.log(`selectedPoints in projector: ${selectedPoints.map(item => item.pointIndex as number)}`);
    // }, [selectedPoints]);


    const getDatasetFromProjectorData = (data: ProjectorData) => {
        console.log(`enter getDatasetFromProjectorData ${JSON.stringify(data)}`);
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
        setDataset(dataset);
        console.log(`exit getDatasetFromProjectorData with dataset=${JSON.stringify(dataset)}`);

        return dataset;
    }

    // When projectorData changes, update the projector
    useEffect(() => {
        if (!scatterGLRef.current || !projectorData) {
            return;
        }
        console.log(`enter projectorData change`);

        const dataset = getDatasetFromProjectorData(projectorData);
        scatterGLRef.current.render(dataset);
        console.log(`exit projectorData change`);

    }, [projectorData]);

    // When datasetId changes, update the projector data
    useEffect(() => {
        const getAsync = async () => {
            console.log(`enter datasetId change`);
            const data = await getProjectorData(datasetId, apiToken) as ProjectorData;
            resetPoints();
            updateProjectorData(data);
            console.log(`exit datasetId change`);
        }
        if (datasetId && apiToken) {
            getAsync();
        }

    }, [datasetId, apiToken]);

    // Initialize the canvas
    useEffect(() => {
        const setupAsync = async () => {
            if (!containerRef.current) {
                return;
            }
            console.log(`Start mount`);

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
                        selectPointHandler(pointIndex);
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

            console.log(`End mount`);

            // Clean up function for removing the resize listener when the component unmounts
            return () => {
                window.removeEventListener('resize', resizeFunc);
                inputElements?.forEach((inputElement) => {
                    inputElement.removeEventListener('change', handleInputChange);
                });
            }
        }
        setupAsync();
    }, []);  // Empty array means this effect runs once on mount and clean up on unmount

    // Your button and input handlers go here...
    const selectPointHandler = (id: number) => {
        console.log(`selectPointHandler ${id} of type ${typeof id}`);
        addPoint(id);
    };

    const selectRandomHandler = () => {
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
                    <div id="messages" ref={messagesRef} style={{ flex: 1 }} />
                </Stack>
            </VStack>
        </Box>
    );
}

export default Projector;
