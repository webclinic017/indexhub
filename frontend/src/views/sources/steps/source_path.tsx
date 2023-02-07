import React, { useState } from "react";
import { Box, Button, Divider, Flex, FormControl, FormLabel, Input, InputGroup, InputLeftAddon, Stack } from '@chakra-ui/react'

const SourcePath = (
  props:{
    setSourceName: React.Dispatch<React.SetStateAction<string>>, 
    setS3DataBucket: React.Dispatch<React.SetStateAction<string>>,
    setRawSourcePath: React.Dispatch<React.SetStateAction<string>>,
    submitSourcePath: () => void,
  }
  ) => {
    return (
        <Box as="form" borderColor="forms.border" borderWidth="1px" borderStyle="solid" borderRadius="lg">
          <Stack spacing="5" px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
            <FormControl isRequired>
                <FormLabel>S3 Data Bucket</FormLabel>
                <InputGroup>
                  <Input onChange={(e) => props.setS3DataBucket(e.currentTarget.value)} placeholder="Name of the S3 bucket containing your source data" />
                  <Input onChange={(e) => props.setRawSourcePath(e.currentTarget.value)} placeholder="Path to the source data files in your S3 Bucket" />
                </InputGroup>
            </FormControl>
            <FormControl isRequired>
                <FormLabel>Source name</FormLabel>
                <Input onChange={(e) => props.setSourceName(e.currentTarget.value)} placeholder="Name for your new source" />
            </FormControl>
          </Stack>
          <Divider />
          <Flex direction="row-reverse" py="4" px={{ base: '4', md: '6' }}>
            <Button onClick={() => props.submitSourcePath()} colorScheme="facebook">
              Next
            </Button>
          </Flex>
        </Box>
    )
}

export default SourcePath