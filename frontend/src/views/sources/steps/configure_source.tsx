import React from "react";
import {
  Box,
  Button,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Stack,
} from "@chakra-ui/react";
import { Select, MultiValue } from "chakra-react-select";

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
  submitSourceConfig: () => void;
  goToPrevStep: () => void;
  setTimeCol: React.Dispatch<React.SetStateAction<string>>;
  setFreq: React.Dispatch<React.SetStateAction<string>>;
  setEntityCols: React.Dispatch<React.SetStateAction<string[]>>;
}) => {
  const options = getOptions(props.column_options);
  const dataset_configs: Record<any, any> = {}
  return (
    <Box
      as="form"
      borderColor="forms.border"
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="lg"
    >
      <Stack
        spacing="5"
        px={{ base: "4", md: "6" }}
        py={{ base: "5", md: "6" }}
      >
        {Object.keys(props.datasets_schema["transaction"]["data_fields"]).map(
          (config_field: string, idx: number) => {
            const has_values = props.datasets_schema["transaction"]["data_fields"][config_field][
              "values"
            ]
              ? true
              : false;

            const is_multiple = props.datasets_schema["transaction"]["data_fields"][config_field][
              "is_multiple"
            ]
              ? true
              : false;

            // const is_required = props.datasets_schema["transaction"]["data_fields"][config_field][
            //   "is_required"
            // ]
            //   ? true
            //   : false;

            return (
              <FormControl isRequired key={idx}>
                <FormLabel>
                  {props.datasets_schema["transaction"]["data_fields"][config_field]["title"]}
                </FormLabel>
                <Select
                  isMulti={is_multiple ? true : false}
                  onChange={(value) => {
                    dataset_configs[config_field] = value
                      ? is_multiple
                        ? getValuesArray(value)
                        : value.value
                      : "";
                  }}
                  useBasicStyles
                  options={has_values ?
                    getOptionsArray(
                      props.datasets_schema["transaction"]["data_fields"][config_field]["values"]
                    ) : options
                  }
                />
              </FormControl>
            );
          }
        )}
      </Stack>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          ml="2rem"
          onClick={() => props.submitSourceConfig()}
          colorScheme="facebook"
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
