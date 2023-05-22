import React, { useContext } from "react";
import { Stack, Text, ListItem, OrderedList, Button, Box } from '@chakra-ui/react';
import { TrendsContext } from "./trends";

const TrendsSidebar = () => {
    const { selectedPoints, removePoint } = useContext(TrendsContext);
    return (
        <Box id="trends-sidebar" height="full" maxH='100%' maxW={'md'} boxShadow="xs" margin="5px">
            <Stack height="full" w={'full'} maxW={'md'}>
                {selectedPoints.length <= 0 ? (<Text fontSize={{ base: 'md', lg: 'lg' }} color={'gray.500'}>
                    Each point is a time series embedding.
                    Click on a point to add it to the list below.

                </Text>) : (
                    <OrderedList>
                        {selectedPoints.map((item, index) => (
                            <ListItem key={index}>
                                <Stack direction='row' spacing={4} align='center' margin={"5px"}>
                                    <Text fontSize={{ base: 'md', lg: 'lg' }} color={'gray.500'}>
                                        label={item.label} labelIndex={item.labelIndex} pointIndex={item.pointIndex}
                                    </Text>
                                    <Button size='xs' colorScheme='red' onClick={() => {
                                        removePoint(item.pointIndex as number);
                                    }}>
                                        Remove
                                    </Button>
                                </Stack>
                            </ListItem>
                        ))}
                    </OrderedList>)}
            </Stack>
        </Box>
    )
}

export default TrendsSidebar;