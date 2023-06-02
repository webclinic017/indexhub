import React from "react";
import {
  Box,
  Button,
  Divider,
  FormControl,
  FormLabel,
  HStack,
  Input,
  Stack,
} from "@chakra-ui/react";

const SourceCredentials = (props: {
  required_credentials_schema: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  submitSourceCreds: (source_creds: Record<string, string>) => Promise<void>;
}) => {
  const source_credentials: Record<string, string> = {};
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
        {Object.keys(props.required_credentials_schema).map(
          (credential, idx) => {
            return (
              <FormControl isRequired key={idx}>
                <FormLabel>
                  {props.required_credentials_schema[credential]["title"]}
                </FormLabel>
                <Input
                  type="password"
                  onChange={(e) => {
                    source_credentials[credential] = e.target.value;
                  }}
                ></Input>
              </FormControl>
            );
          }
        )}
      </Stack>
      <Divider />
      <HStack p="4" justifyContent="flex-end">
        <Button
          onClick={() => {
            props.submitSourceCreds(source_credentials);
          }}
        >
          Submit
        </Button>
      </HStack>
    </Box>
  );
};

export default SourceCredentials;
