import React from "react";
import {
  Box,
  Divider,
  Grid,
  HStack,
  Spinner,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Card, CardBody } from "@chakra-ui/card";
import { capitalizeFirstLetter } from "../../../utilities/helpers";
import { ReactComponent as S3Logo } from "../../../assets/images/svg/s3.svg";
import { ReactComponent as AzureLogo } from "../../../assets/images/svg/azure.svg";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCircleDot } from "@fortawesome/pro-light-svg-icons";
import { colors } from "../../../theme/theme";

const logos: Record<string, any> = {
  s3: <S3Logo width="7rem" height="7rem" />,
  azure: <AzureLogo width="7rem" height="7rem" />,
};

const SourceType = (props: {
  conn_schema: Record<string, any>;
  submitSourceType: (source_tag: string) => void;
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
        {Object.keys(props.conn_schema).length > 0 ? (
          <Grid templateColumns="repeat(3, 1fr)" gap={6}>
            {Object.keys(props.conn_schema).map((source_tag, idx) => {
              return (
                <Card
                  cursor="pointer"
                  boxShadow="md"
                  borderRadius="lg"
                  key={idx}
                  onClick={() => {
                    props.submitSourceType(source_tag);
                  }}
                >
                  <CardBody>
                    <VStack>
                      <HStack p="3" width="100%" justify="left">
                        <FontAwesomeIcon
                          size="2xs"
                          icon={faCircleDot as any}
                          beatFade
                          style={{
                            color:
                              props.conn_schema[source_tag][
                                "is_authenticated"
                              ] == true
                                ? colors.supplementary.indicators.main_green
                                : colors.supplementary.indicators.main_red,
                          }}
                        />
                        <Text
                          textAlign="center"
                          fontSize="2xs"
                          color={
                            props.conn_schema[source_tag]["is_authenticated"] ==
                            true
                              ? colors.supplementary.indicators.main_green
                              : colors.supplementary.indicators.main_red
                          }
                        >
                          {props.conn_schema[source_tag]["is_authenticated"] ==
                          true
                            ? "HAS CREDENTIALS"
                            : "NEEDS CREDENTIALS"}
                        </Text>
                      </HStack>
                      <Box p="6">{logos[source_tag]}</Box>
                      <Box p="4">
                        <Text textAlign="center" fontWeight="bold">
                          {capitalizeFirstLetter(source_tag)}
                        </Text>
                      </Box>
                    </VStack>
                  </CardBody>
                </Card>
              );
            })}
          </Grid>
        ) : (
          <Stack alignItems="center" justifyContent="center" height="full">
            <Spinner />
            <Text>Loading...</Text>
          </Stack>
        )}
      </Stack>
      <Divider />
    </Box>
  );
};

export default SourceType;
