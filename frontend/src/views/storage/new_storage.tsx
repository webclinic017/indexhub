import { Container, Stack, useToast } from "@chakra-ui/react";
import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { AppState } from "../..";
import { Step } from "../../components/step";
import Toast from "../../components/toast";
import {
  createStorage,
  getStorageSchema,
} from "../../utilities/backend_calls/user";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { useStep } from "../../utilities/hooks/useStep";
import StorageConfig from "./steps/storage_config";
import StorageType from "./steps/storage_type";

const steps = [
  {
    title: "Step 1",
    description: "Your storage type",
  },
  {
    title: "Step 2",
    description: "Your storage configurations",
  },
];

const NewStorage = () => {
  const [storage_schema, setStorageSchema] = useState<Record<string, any>>({}); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [storage_type, setStorageType] = useState("");
  const access_token_indexhub_api = useAuth0AccessToken();
  const [currentStep, { goToNextStep, goToPrevStep }] = useStep({
    maxStep: steps.length,
  });
  const user_details = useSelector((state: AppState) => state.reducer?.user);
  const toast = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    const getStorageSchemaApi = async () => {
      const storage_schema = await getStorageSchema(access_token_indexhub_api);
      setStorageSchema(storage_schema);
    };
    if (access_token_indexhub_api) {
      getStorageSchemaApi();
    }
  }, [access_token_indexhub_api]);

  const submitStorageType = (storage_type: string) => {
    setStorageType(storage_type);
    goToNextStep();
  };

  const submitStorageConfig = (
    storage_credentials: Record<string, string>,
    bucket_name: string
  ) => {
    const createStorageApi = async () => {
      const response = await createStorage(
        storage_credentials,
        bucket_name,
        storage_type,
        user_details.id,
        access_token_indexhub_api
      );
      if (Object.keys(response).includes("ok")) {
        navigate("/sources");
        Toast(
          toast,
          "Credentials Stored",
          `Credentials for your ${storage_type} storage have been securely stored`,
          "success"
        );
      } else {
        Toast(toast, "Error", response["detail"], "error");
      }
    };

    if (
      Object.keys(storage_schema[storage_type]).every((variable) =>
        Object.keys(storage_credentials).includes(variable)
      ) &&
      bucket_name
    ) {
      createStorageApi();
    } else {
      Toast(
        toast,
        "Empty / Invalid Columns",
        "Please ensure all required columns are filled with valid values",
        "error"
      );
    }
  };

  const stepScreens: Record<number, JSX.Element> = {
    0: (
      <StorageType
        storage_schema={storage_schema}
        submitStorageType={submitStorageType}
      />
    ),
    1: (
      <StorageConfig
        selected_storage_schema={storage_schema[storage_type]}
        goToPrevStep={goToPrevStep}
        submitStorageConfig={submitStorageConfig}
      />
    ),
  };
  return (
    <Container maxWidth="920px" py={{ base: "8", md: "16" }}>
      <Stack direction={{ base: "column", md: "row" }} spacing="4" mb="3rem">
        {steps.map((step, id) => (
          <Step
            key={id}
            title={step.title}
            description={step.description}
            isActive={currentStep === id}
            isCompleted={currentStep > id}
          />
        ))}
      </Stack>
      {stepScreens[currentStep]}
    </Container>
  );
};

export default NewStorage;
