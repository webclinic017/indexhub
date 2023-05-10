import { Box, Divider, Grid, Stack, Text, VStack } from "@chakra-ui/react";
import { Card, CardBody } from "@chakra-ui/card";
import React from "react";
import { capitalizeFirstLetter } from "../../../utilities/helpers";

const ObjectiveType = (props: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  objectives_schema: Record<any, any>;
  submitObjectiveType: (objective_type: string) => void;
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
          {Object.keys(props.objectives_schema).map((objective_type, idx) => {
            return (
              <Card
                cursor="pointer"
                boxShadow="md"
                borderRadius="lg"
                key={idx}
                onClick={() => {
                  props.submitObjectiveType(objective_type);
                }}
              >
                <CardBody>
                  <VStack>
                    {/* <Box p="6">{logos[source_type]}</Box> */}
                    <Box p="4">
                      <Text textAlign="center" fontWeight="bold">
                        {capitalizeFirstLetter(objective_type).replaceAll("_", " ")}
                      </Text>
                    </Box>
                    <Box p="1" width="100%" borderBottomRadius="lg">
                      <Text textAlign="center" fontSize="small">
                        {props.objectives_schema[objective_type]["description"]}
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

export default ObjectiveType;
