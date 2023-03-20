import React from "react";
import { Box, Divider, Grid, Stack, Text, VStack } from "@chakra-ui/react";
import { Card, CardBody } from "@chakra-ui/card";
import { capitalizeFirstLetter } from "../../../utilities/helpers";
import { ReactComponent as S3Logo } from "../../../assets/images/svg/s3.svg";
import { ReactComponent as AzureLogo } from "../../../assets/images/svg/azure.svg";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const logos: Record<string, any> = {
  s3: <S3Logo width="7rem" height="7rem" />,
  azure: <AzureLogo width="7rem" height="7rem" />,
};

const SourceType = (props: {
  sources_schema: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  submitSourceType: (source_type: string) => void;
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
          {Object.keys(props.sources_schema).map((source_type, idx) => {
            return (
              <Card
                cursor="pointer"
                boxShadow="md"
                borderRadius="lg"
                key={idx}
                onClick={() => {
                  props.submitSourceType(source_type);
                }}
              >
                <CardBody>
                  <VStack>
                    <Box p="6">{logos[source_type]}</Box>
                    <Box p="4">
                      <Text textAlign="center" fontWeight="bold">
                        {capitalizeFirstLetter(source_type)}
                      </Text>
                    </Box>
                    <Box
                      p="3"
                      backgroundColor={
                        props.sources_schema[source_type]["is_authenticated"] ==
                        true
                          ? "buttons.main_green"
                          : "buttons.filter_grey"
                      }
                      width="100%"
                      borderBottomRadius="lg"
                    >
                      <Text textAlign="center" fontWeight="bold">
                        {props.sources_schema[source_type][
                          "is_authenticated"
                        ] == true
                          ? "Has Credentials"
                          : "Needs Credentials"}
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

export default SourceType;
