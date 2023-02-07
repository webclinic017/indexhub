import React from "react"
import { Box, Divider, FormControl, FormLabel, Stack, Text } from "@chakra-ui/react"
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


const NewReport = (
    props: {
        source_name: string,
        entity_cols: string[],
        target_cols: string[],
        setSelectedLevelCols: React.Dispatch<React.SetStateAction<never[]>>
        setSelectedTargetCol: React.Dispatch<React.SetStateAction<string>>
    }
) => {
    

    return (
        <Box as="form" borderColor="forms.border" borderWidth="1px" borderStyle="solid" borderRadius="lg">
          <Stack spacing="5" px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }}>
            <Text>Source name: <b>{props.source_name}</b></Text>
            <FormControl isRequired>
                <FormLabel>Target column</FormLabel>
                <Select onChange={(value) => props.setSelectedTargetCol(value ? value.value : "")} options={getOptions(props.target_cols)}/>
            </FormControl>
            <FormControl isRequired>
                <FormLabel>Level(s)</FormLabel>
                <Select onChange={(value) => setColumnValue(value, props.setSelectedLevelCols)} options={getOptions(props.entity_cols)} isMulti/>
            </FormControl>
          </Stack>
          <Divider />
        </Box>
    )
}

export default NewReport