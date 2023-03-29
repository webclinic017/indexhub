import { Box, Divider, Grid, Stack, Text, VStack } from "@chakra-ui/react";
import { Card, CardBody } from "@chakra-ui/card";
import React from "react";
import { capitalizeFirstLetter } from "../../../utilities/helpers";

const PolicyType = (props: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  policies_schema: Record<any, any>;
  submitPolicyType: (policy_type: string) => void;
}) => {
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
        <Grid templateColumns="repeat(3, 1fr)" gap={6}>
          {Object.keys(props.policies_schema).map((policy_type, idx) => {
            return (
              <Card
                cursor="pointer"
                boxShadow="md"
                borderRadius="lg"
                key={idx}
                onClick={() => {
                  props.submitPolicyType(policy_type);
                }}
              >
                <CardBody>
                  <VStack>
                    {/* <Box p="6">{logos[source_type]}</Box> */}
                    <Box p="4">
                      <Text textAlign="center" fontWeight="bold">
                        {capitalizeFirstLetter(policy_type)}
                      </Text>
                    </Box>
                    <Box p="1" width="100%" borderBottomRadius="lg">
                      <Text textAlign="center" fontSize="small">
                        {props.policies_schema[policy_type]["subtitle"]}
                      </Text>
                    </Box>
                  </VStack>
                </CardBody>
              </Card>
            );
          })}
        </Grid>
      </Stack>
      <Divider />
    </Box>
  );
};

export default PolicyType;
