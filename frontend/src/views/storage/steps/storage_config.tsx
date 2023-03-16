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
import React from "react";

const StorageConfig = (props: {
  selected_storage_schema: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  goToPrevStep: () => void;
  submitStorageConfig: (
    storage_credentials: Record<string, string>,
    bucket_name: string
  ) => void;
}) => {
  const storage_credentials: Record<string, string> = {};
  let bucket_name = "";
  console.log(props.selected_storage_schema);
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
        {Object.keys(props.selected_storage_schema).map((credential, idx) => {
          return (
            <FormControl isRequired key={idx}>
              <FormLabel>
                {props.selected_storage_schema[credential]["title"]}
              </FormLabel>
              <Input
                onChange={(e) => {
                  storage_credentials[credential] = e.target.value;
                }}
              ></Input>
            </FormControl>
          );
        })}
        <FormControl isRequired>
          <FormLabel>Bucket Name</FormLabel>
          <Input
            onChange={(e) => {
              bucket_name = e.target.value;
            }}
          ></Input>
        </FormControl>
        {/* {Object.keys(schema_variables).map((variable: string, idx: number) => {
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
            </FormControl> */}
      </Stack>
      <Divider />
      <Flex direction="row-reverse" py="4" px={{ base: "4", md: "6" }}>
        <Button
          ml="2rem"
          onClick={() =>
            props.submitStorageConfig(storage_credentials, bucket_name)
          }
          colorScheme="facebook"
        >
          Create Storage
        </Button>
        <Button onClick={() => props.goToPrevStep()} colorScheme="facebook">
          Prev
        </Button>
      </Flex>
    </Box>
  );
};

export default StorageConfig;
