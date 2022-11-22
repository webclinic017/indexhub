import React from "react";
import { Outlet } from "react-router-dom";

export default function NestedPage() {
  return (
    <>
      <p>This is a page with nested views</p>
      <Outlet />
    </>
  );
}
