import React from "react";
import { Box, Button, Divider, Flex, FormControl, FormLabel, Input, Stack } from '@chakra-ui/react'
import { Select, MultiValue } from "chakra-react-select"

const setColumnValue = (values: MultiValue<Record<any, string>>, set_func: any) => {
  const columns: string[] = []
  values.map((value) => {
    columns.push(value.value)
  })
  set_func(columns)
}

const getOptions = (options: string[]) => {
  const result: Record<any, string>[] = []
  options.forEach((option) => {
    result.push(
      {
        value: option,
        label: option
      }
    )
  })
  return result
}

const ConfigureSource = (props: {
  column_options: string[],
  submitSourceConfig: () => void,
  goToPrevStep: () => void,
  setTimeCol: React.Dispatch<React.SetStateAction<string>>,
  setFreq: React.Dispatch<React.SetStateAction<string>>,
  setEntityCols: React.Dispatch<React.SetStateAction<never[]>>,
  setTargetCols: React.Dispatch<React.SetStateAction<never[]>>,
  setManualForecastPath: React.Dispatch<React.SetStateAction<string>>
}) => {
    const options = getOptions(props.column_options)

    return (
        <Box as="form" borderColor="forms.border" borderWidth="1px" borderStyle="solid" borderRadius="lg">
          <Stack spacing="5" px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
            <Stack spacing="6" direction={{ base: 'column', md: 'row' }}>
                <FormControl isRequired>
                    <FormLabel>Time column</FormLabel>
                    <Select onChange={(value) => props.setTimeCol(value ? value.value : "")} options={options} useBasicStyles/>
                </FormControl>
                <FormControl isRequired>
                    <FormLabel>Frequency</FormLabel>
                    <Select
                      defaultValue={{
                        label: "Daily",
                        value: "d"
                      }}
                      onChange={(value) => props.setFreq(value ? value.value : "")}
                      useBasicStyles
                      options={[
                        {
                          label: "Daily",
                          value: "d"
                        },
                        {
                          label: "Weekly",
                          value: "w"
                        },
                        {
                          label: "Monthly",
                          value: "m"
                        },
                        {
                          label: "Quarterly",
                          value: "q"
                        },
                      ]}
                    />
                </FormControl>
            </Stack>
            <FormControl isRequired>
                <FormLabel>Entity columns</FormLabel>
                <Select onChange={(value) => setColumnValue(value, props.setEntityCols)} options={options} isMulti/>
            </FormControl>
            <FormControl isRequired>
                <FormLabel>Target columns</FormLabel>
                <Select onChange={(value) => setColumnValue(value, props.setTargetCols)} options={options} isMulti/>
            </FormControl>
            <FormControl isRequired>
                <FormLabel>Manual forecast path</FormLabel>
                <Input onChange={(e) => props.setManualForecastPath(e.currentTarget.value)} placeholder="Path to the manual forecast files in your S3 Bucket" />
            </FormControl>
          </Stack>
          <Divider />
          <Flex direction="row-reverse" py="4" px={{ base: '4', md: '6' }}>
            <Button ml="2rem" onClick={() => props.submitSourceConfig()} colorScheme="facebook">
              Next
            </Button>
            <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
              Prev
            </Button>
          </Flex>
        </Box>
    )
}

export default ConfigureSource