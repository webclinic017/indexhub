import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  Card,
  CardBody,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  HStack,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Select, MultiValue } from "chakra-react-select";
import { capitalizeFirstLetter } from "../../../utilities/helpers";

const setColumnValue = (
  values: MultiValue<Record<any, string>>, // eslint-disable-line @typescript-eslint/no-explicit-any
  set_func: any // eslint-disable-line @typescript-eslint/no-explicit-any
) => {
  const columns: string[] = [];
  values.map((value) => {
    columns.push(value.value);
  });
  set_func(columns);
};

const getOptions = (options: string[]) => {
  const result: Record<any, string>[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  options.forEach((option) => {
    result.push({
      value: option,
      label: option,
    });
  });
  return result;
};

const getOptionsArray = (options: string[]) => {
  const result_options: any[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  options.forEach((option: string) => {
    result_options.push({
      label: option,
      value: option,
    });
  });
  return result_options;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getValuesArray = (values: MultiValue<Record<any, string>>) => {
  const values_array: string[] = [];
  values.map((value) => {
    values_array.push(value.value);
  });
  return values_array;
};

const ConfigureSource = (props: {
  column_options: string[];
  datasets_schema: Record<any, any>;
  submitSourceConfig: (datasetConfigs: Record<any, any>, datasetType: string) => void
  goToPrevStep: () => void;
}) => {
  const options = getOptions(props.column_options);
  const [datasetConfigs, setDatasetConfigs] = useState<Record<any, any>>({})
  const [datasetType, setDatasetType] = useState<string | null>(null)


  return (
    <Box
      as="form"
      borderColor="forms.border"
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="lg"
    >
      <HStack width="100%">
        {Object.keys(props.datasets_schema).map((source_type, idx) => {
          return (
            <Card
              width="50%"
              cursor="pointer"
              boxShadow="md"
              borderRadius="lg"
              key={idx}
              backgroundColor={datasetType == source_type ? "table.header_background" : ""}
              onClick={() => {
                setDatasetType(source_type)
              }}
            >
              <CardBody>
                <VStack>
                  {/* <Box p="6">{logos[source_type]}</Box> */}
                  <Box p="4">
                    <Text textAlign="center" fontWeight="bold">
                      {capitalizeFirstLetter(source_type).replaceAll("_", " ")}
                    </Text>
                  </Box>
                  <Box p="1" width="100%" borderBottomRadius="lg">
                    <Text textAlign="center" fontSize="small">
                      {props.datasets_schema[source_type]["description"]}
                    </Text>
                  </Box>
                </VStack>
              </CardBody>
            </Card>
          )
        })}
      </HStack>
      {datasetType ? (
        <Stack
          spacing="5"
          px={{ base: "4", md: "6" }}
          py={{ base: "5", md: "6" }}
          height="20rem"
          overflowX="scroll"
        >
          {Object.keys(props.datasets_schema[datasetType]["data_fields"]).map(
            (config_field: string, idx: number) => {
              const has_values = props.datasets_schema[datasetType]["data_fields"][config_field][
                "values"
              ]
                ? true
                : false;

              const is_multiple = props.datasets_schema[datasetType]["data_fields"][config_field][
                "is_multiple"
              ]
                ? true
                : false;

              const is_required = props.datasets_schema[datasetType]["data_fields"][config_field][
                "is_required"
              ]
                ? true
                : false;

              return (
                <FormControl isRequired={is_required} key={idx}>
                  <FormLabel>
                    {props.datasets_schema[datasetType]["data_fields"][config_field]["title"]}
                  </FormLabel>
                  <Select
                    isMulti={is_multiple ? true : false}
                    onChange={(value) => {
                      datasetConfigs[config_field] = value
                        ? is_multiple
                          ? getValuesArray(value)
                          : value.value
                        : "";
                      setDatasetConfigs(structuredClone(datasetConfigs))
                    }}
                    useBasicStyles
                    options={has_values ?
                      getOptionsArray(
                        props.datasets_schema[datasetType]["data_fields"][config_field]["values"]
                      ) : options
                    }
                  />
                </FormControl>
              );
            }
          )}
        </Stack>
      ) : (
        <Stack alignItems="center" justify="center" height="20rem">
          <Text> Choose a source type</Text>
        </Stack>
      )}

      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          ml="2rem"
          onClick={() => datasetType ? props.submitSourceConfig(datasetConfigs, datasetType) : {}}
          colorScheme="facebook"
          isDisabled={!datasetType}
        >
          Next
        </Button>
        <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
          Prev
        </Button>
      </Flex>
    </Box>
  );
};

export default ConfigureSource;
