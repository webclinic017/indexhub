import { AppState } from "../../index";
import {
  Flex,
  HStack,
  Text,
  VStack,
  Heading,
  Stack,
  Box,
} from "@chakra-ui/react";
import { Card, CardBody } from "@chakra-ui/card";
import React from "react";
import { useSelector } from "react-redux";
import NewStorage from "./new_storage";
import { ReactComponent as S3Logo } from "../../assets/images/svg/s3.svg";
import { ReactComponent as AzureLogo } from "../../assets/images/svg/azure.svg";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCalendarDays } from "@fortawesome/pro-light-svg-icons";
import { capitalizeFirstLetter } from "../../utilities/helpers";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const logos: Record<string, any> = {
  s3: <S3Logo width="7rem" />,
  azure: <AzureLogo width="7rem" />,
};

const Storage = () => {
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  return (
    <>
      {user_details.storage_bucket_name ? (
        <Flex justifyContent="center">
          <Card boxShadow="md" borderRadius="lg" width="50%" p="6">
            <CardBody>
              <HStack justifyContent="center">
                <Box p="6">{logos[user_details.storage_tag]}</Box>

                <VStack alignItems="flex-start">
                  <Heading
                    size="md"
                    fontWeight="extrabold"
                    letterSpacing="tight"
                    marginEnd="6"
                  >
                    {capitalizeFirstLetter(user_details.storage_tag)} Storage
                  </Heading>
                  <Text mt="1" fontWeight="medium">
                    Bucket name: {user_details.storage_bucket_name}
                  </Text>
                  <Stack spacing="1" mt="2">
                    <HStack fontSize="sm">
                      <FontAwesomeIcon icon={faCalendarDays} />
                      <Text>
                        {new Date(
                          user_details.storage_created_at
                        ).toDateString()}
                      </Text>
                    </HStack>
                  </Stack>
                </VStack>
              </HStack>
            </CardBody>
          </Card>
        </Flex>
      ) : (
        <NewStorage />
      )}
    </>
  );
};

export default Storage;
