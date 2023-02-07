import React, { useState } from "react";
import { Box, Button, Divider, Flex, Stack, Text, StackDivider, Container } from '@chakra-ui/react'

const ConfirmCreateSource = (
  props:{
    raw_source_path: string,
    s3_data_bucket: string,
    source_name: string,
    freq: string,
    time_col: string,
    target_cols: string[],
    entity_cols: string[],
    manual_forecast_path: string,
    createSource: () => void,
    goToPrevStep: () => void
  }
  ) => {
    return (
        <Box as="form" borderColor="forms.border" borderWidth="1px" borderStyle="solid" borderRadius="lg">
            <Box bgColor={"forms.bg_grey"} borderTopRadius="lg">
                <Text py="1rem" pl="1rem" color="muted" fontSize="sm">
                    An overview of your new source setup
                </Text>
            </Box>
            <Divider />
            <Container maxWidth="unset" py="1rem">
            <Stack spacing="5">
                
                <Stack spacing="5" divider={<StackDivider />}>
                    <Stack
                        direction={{ base: 'column', md: 'row' }}
                        spacing={{ base: '1.5', md: '8' }}
                        justifyContent="space-between"
                    >
                        <Text width="30%" fontWeight="bold">Source name:</Text>
                        <Text width="70%" >{props.source_name}</Text>
                    </Stack>
                    <Stack
                        direction={{ base: 'column', md: 'row' }}
                        spacing={{ base: '1.5', md: '8' }}
                        justifyContent="space-between"
                    >
                        <Text width="30%" fontWeight="bold">Source path:</Text>
                        <Text width="70%" >s3://{props.s3_data_bucket}/{props.raw_source_path}</Text>
                    </Stack>
                    <Stack
                        direction={{ base: 'column', md: 'row' }}
                        spacing={{ base: '1.5', md: '8' }}
                        justifyContent="space-between"
                    >
                        <Text width="30%" fontWeight="bold">Manual forecast path:</Text>
                        <Text width="70%" >{props.manual_forecast_path}</Text>
                    </Stack>
                    <Stack
                        direction={{ base: 'column', md: 'row' }}
                        spacing={{ base: '1.5', md: '8' }}
                        justifyContent="space-between"
                    >
                        <Text width="30%" fontWeight="bold">Frequency:</Text>
                        <Text width="70%" >{props.freq}</Text>
                    </Stack>
                    <Stack
                        direction={{ base: 'column', md: 'row' }}
                        spacing={{ base: '1.5', md: '8' }}
                        justifyContent="space-between"
                    >
                        <Text width="30%" fontWeight="bold">Time col:</Text>
                        <Text width="70%" >{props.time_col}</Text>
                    </Stack>
                    <Stack
                        direction={{ base: 'column', md: 'row' }}
                        spacing={{ base: '1.5', md: '8' }}
                        justifyContent="space-between"
                    >
                        <Text width="30%" fontWeight="bold">Target column(s)</Text>
                        <Text width="70%" >{props.target_cols.join(", ")}</Text>
                    </Stack>
                    <Stack
                        direction={{ base: 'column', md: 'row' }}
                        spacing={{ base: '1.5', md: '8' }}
                        justifyContent="space-between"
                    >
                        <Text width="30%" fontWeight="bold">Entity column(s)</Text>
                        <Text width="70%" >{props.entity_cols.join(", ")}</Text>
                    </Stack>
                </Stack>
            </Stack>
            </Container>
            <Divider />
            <Flex direction="row-reverse" py="4" px={{ base: '4', md: '6' }}>
                <Button ml="2rem" onClick={() => props.createSource()} colorScheme="facebook">
                Create source
                </Button>
                <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
                Prev
                </Button>
            </Flex>
        </Box>
    )
}

export default ConfirmCreateSource