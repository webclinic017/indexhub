import React, { useState } from "react";
import { Container, Stack, useToast } from "@chakra-ui/react";
import { useEffect } from "react";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../..";
import {
  getObjectivesSchema,
  createObjective as createObjectiveApi,
} from "../../utilities/backend_calls/objective";
import ObjectiveType from "./steps/objective_type";
import { Step } from "../../components/step";
import { useStep } from "../../utilities/hooks/useStep";
import ObjectiveSource from "./steps/objective_source";
import Toast from "../../components/toast";
import ObjectiveConfigs from "./steps/objective_configs";
import ConfirmCreateObjective from "./steps/confirm_create_objective";

const steps = [
  {
    title: "Step 1",
    description: "Your objective type",
  },
  {
    title: "Step 2",
    description: "Your objective sources",
  },
  {
    title: "Step 3",
    description: "Configure your objective",
  },
  {
    title: "Step 4",
    description: "Confirm objective creation",
  },
];

const NewObjective = () => {
  const [objectives_schema, setObjectivesSchema] = useState<Record<any, any>>({}); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [objective_configs, setObjectiveConfigs] = useState<Record<string, any>>({}); // eslint-disable-line @typescript-eslint/no-explicit-any
  const access_token_indexhub_api = useAuth0AccessToken();
  const [currentStep, { goToNextStep, goToPrevStep }] = useStep({
    maxStep: steps.length,
  });
  const toast = useToast();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  const submitObjectiveType = (objective_type: string) => {
    objective_configs["objective_type"] = objective_type;
    setObjectiveConfigs(objective_configs);
    goToNextStep();
  };

  const submitObjectiveSources = (objective_sources: Record<string, string>) => {
    if (Object.keys(objective_sources).includes("panel")) {
      objective_configs["panel"] = objective_sources["panel"];
      objective_configs["panel_name"] = objective_sources["panel_name"];
      objective_configs["baseline"] = objective_sources["baseline"]
        ? objective_sources["baseline"]
        : "";
      objective_configs["baseline_name"] = objective_sources["baseline_name"]
        ? objective_sources["baseline_name"]
        : "";
      objective_configs["inventory"] = objective_sources["inventory"]
        ? objective_sources["inventory"]
        : "";
      objective_configs["inventory_name"] = objective_sources["inventory_name"]
        ? objective_sources["inventory_name"]
        : "";
      objective_configs["transaction"] = objective_sources["transaction"]
        ? objective_sources["transaction"]
        : "";
      objective_configs["transaction_name"] = objective_sources["transaction_name"]
        ? objective_sources["transaction_name"]
        : "";
      setObjectiveConfigs(objective_configs);
      goToNextStep();
    } else {
      Toast(
        toast,
        "Empty / Invalid Columns",
        "Please ensure all required columns are filled with valid values",
        "error"
      );
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const submitObjectiveConfigs = (objective_configs: Record<string, any>) => {
    setObjectiveConfigs(objective_configs);
    goToNextStep();
  };

  const createObjective = async () => {
    const create_objective_response = await createObjectiveApi(
      user_details.id,
      objective_configs,
      access_token_indexhub_api
    );
    if (Object.keys(create_objective_response).includes("objective_id")) {
      Toast(
        toast,
        "Objective Created",
        `Your new objective (${objective_configs["objective_name"]}) was successfuly created`,
        "success"
      );
      // navigate("/sources");
    } else {
      Toast(toast, "Error", create_objective_response["detail"], "error");
    }
  };

  const stepScreens: Record<number, JSX.Element> = {
    0: (
      <ObjectiveType
        objectives_schema={objectives_schema}
        submitObjectiveType={submitObjectiveType}
      />
    ),
    1: (
      <ObjectiveSource
        objectives_schema={objectives_schema}
        objective_configs={objective_configs}
        submitObjectiveSources={submitObjectiveSources}
        goToPrevStep={goToPrevStep}
      />
    ),
    2: (
      <ObjectiveConfigs
        objectives_schema={objectives_schema}
        objective_configs={objective_configs}
        submitObjectiveConfigs={submitObjectiveConfigs}
        goToPrevStep={goToPrevStep}
      />
    ),
    3: (
      <ConfirmCreateObjective
        objective_configs={objective_configs}
        createObjective={createObjective}
        goToPrevStep={goToPrevStep}
      />
    ),
  };

  useEffect(() => {
    const getObjectivesSchemaApi = async () => {
      const objectives_schema = await getObjectivesSchema(
        user_details.id,
        access_token_indexhub_api
      );
      setObjectivesSchema(objectives_schema);
    };
    if (access_token_indexhub_api && user_details.id) {
      getObjectivesSchemaApi();
    }
  }, [access_token_indexhub_api, user_details]);

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

export default NewObjective;
