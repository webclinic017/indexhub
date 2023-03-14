import React from "react";
import {
  Box,
  Button,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Input,
  Stack,
} from "@chakra-ui/react";
import { Select } from "chakra-react-select";

const getOptions = (options: string[]) => {
  const result_options: any[] = []; // eslint-disable-line @typescript-eslint/no-explicit-any
  options.forEach((option: string) => {
    result_options.push({
      label: option,
      value: option,
    });
  });
  return result_options;
};

const SourcePath = (props: {
  source_type: string;
  sources_schema: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  goToPrevStep: () => void;
  submitSourcePath: (configs: Record<string, string>) => Promise<void>;
}) => {
  const configs: Record<string, string> = {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const schema_variables: Record<string, any> =
    props.sources_schema[props.source_type]["variables"];
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
        {Object.keys(schema_variables).map((variable: string, idx: number) => {
          const has_values = Object.keys(schema_variables[variable]).includes(
            "values"
          );
          return (
            <FormControl isRequired key={idx}>
              <FormLabel>{schema_variables[variable]["title"]}</FormLabel>
              {!has_values && (
                <Input
                  onChange={(e) => (configs[variable] = e.currentTarget.value)}
                  placeholder="Name for your new source"
                />
              )}
              {has_values && (
                <Select
                  onChange={(value) =>
                    (configs[variable] = value ? value.value : "")
                  }
                  useBasicStyles
                  options={getOptions(schema_variables[variable]["values"])}
                />
              )}
            </FormControl>
          );
        })}
        <FormControl isRequired>
          <FormLabel>Source name</FormLabel>
          <Input
            onChange={(e) => (configs["source_name"] = e.currentTarget.value)}
            placeholder="Name for your new source"
          />
        </FormControl>
      </Stack>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          onClick={() => props.submitSourcePath(configs)}
          colorScheme="facebook"
          ml="2rem"
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

export default SourcePath;
