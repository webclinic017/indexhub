import React from "react";
import { Box, Divider, Grid, Stack, Text, VStack } from "@chakra-ui/react";
import { Card, CardBody } from "@chakra-ui/card";
import { capitalizeFirstLetter } from "../../../utilities/helpers";
import { ReactComponent as S3Logo } from "../../../assets/images/svg/s3.svg";
import { ReactComponent as AzureLogo } from "../../../assets/images/svg/azure.svg";

const logos: Record<string, any> = {
  s3: <S3Logo width="7rem" height="7rem" />,
  azure: <AzureLogo width="7rem" height="7rem" />,
};

const StorageType = (props: {
  storage_schema: Record<string, any>;
  submitStorageType: (storage_type: string) => void;
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
          {Object.keys(props.storage_schema).map((storage_type, idx) => {
            return (
              <Card
                cursor="pointer"
                boxShadow="md"
                borderRadius="lg"
                key={idx}
                onClick={() => {
                  props.submitStorageType(storage_type);
                }}
              >
                <CardBody>
                  <VStack>
                    <Box p="6">{logos[storage_type]}</Box>
                    <Box p="4">
                      <Text textAlign="center" fontWeight="bold">
                        {capitalizeFirstLetter(storage_type)}
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

export default StorageType;
